"""
VC Data Search Agent
Searches the internet to collect VC industry knowledge from blogs, websites, and publications
"""
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
from urllib.parse import urlparse, urljoin

# Try to import DuckDuckGo search
try:
    from duckduckgo_search import DDGS
    DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False

logger = logging.getLogger(__name__)


class VCDataSearchAgent:
    """Agent that searches for and collects VC industry knowledge"""
    
    def __init__(self):
        self.logger = logger
        self._test_ddg_connection()
    
    def _test_ddg_connection(self):
        """Test if DuckDuckGo search is working"""
        if DDG_AVAILABLE:
            try:
                with DDGS() as ddgs:
                    # Try a simple test search
                    test_results = list(ddgs.text("venture capital", max_results=1))
                    if test_results:
                        self.logger.info("✅ DuckDuckGo search is working")
                    else:
                        self.logger.warning("⚠️ DuckDuckGo search returned no results (may be rate limited)")
            except Exception as e:
                self.logger.warning(f"⚠️ DuckDuckGo connection test failed: {e}")
        else:
            self.logger.warning("⚠️ DuckDuckGo not available - will use fallback scraping only")
        
        # Known VC firm blogs and websites
        self.vc_firm_sites = [
            'a16z.com',
            'sequoiacap.com',
            'accel.com',
            'bvp.com',  # Bessemer
            'firstround.com',
            'usv.com',  # Union Square Ventures
            'benchmark.com',
            'greylock.com',
            'insights.khoslaventures.com',
            'blog.ycombinator.com',
        ]
        
        # Founder blogs
        self.founder_blogs = [
            'paulgraham.com',
            'pmarca.com',  # Marc Andreessen
            'avc.com',  # Fred Wilson
            'feld.com',  # Brad Feld
        ]
        
        # Industry publications
        self.industry_publications = [
            'techcrunch.com',
            'venturebeat.com',
            'theinformation.com',
            'pitchbook.com',
            'cbinsights.com',
        ]
    
    def search_vc_knowledge(self, max_results_per_source: int = 20) -> List[Dict]:
        """
        Search for VC industry knowledge from multiple sources
        
        Args:
            max_results_per_source: Maximum results to collect per source type
            
        Returns:
            List of knowledge items with content, source, and metadata
        """
        all_knowledge = []
        
        # Search queries for VC knowledge
        search_queries = [
            'venture capital best practices',
            'VC due diligence process',
            'startup valuation methods',
            'venture capital market analysis',
            'VC investment criteria',
            'startup evaluation framework',
            'venture capital industry benchmarks',
            'VC market trends',
            'startup funding stages',
            'venture capital deal terms',
            'VC portfolio company analysis',
            'venture capital market size',
            'startup exit strategies',
            'VC investment thesis',
            'venture capital market pace',
        ]
        
        if DDG_AVAILABLE:
            try:
                self.logger.info("Starting DuckDuckGo search for VC knowledge...")
                with DDGS() as ddgs:
                    queries_processed = 0
                    for query in search_queries:
                        try:
                            queries_processed += 1
                            self.logger.debug(f"Searching query {queries_processed}/{len(search_queries)}: {query}")
                            
                            # Search for VC knowledge on specific sites
                            try:
                                results = list(ddgs.text(
                                    f"{query} site:a16z.com OR site:sequoiacap.com OR site:firstround.com OR site:avc.com",
                                    max_results=5
                                ))
                                self.logger.debug(f"Found {len(results)} results for site-specific search")
                                
                                for result in results:
                                    if result.get('href') and result.get('body'):
                                        knowledge_item = {
                                            'title': result.get('title', ''),
                                            'url': result.get('href', ''),
                                            'content': result.get('body', ''),
                                            'source_type': 'vc_blog',
                                            'query': query,
                                        }
                                        all_knowledge.append(knowledge_item)
                            except Exception as e:
                                self.logger.warning(f"Site-specific search failed for '{query}': {e}")
                            
                            # Also search general VC knowledge
                            try:
                                general_results = list(ddgs.text(
                                    query,
                                    max_results=5
                                ))
                                self.logger.debug(f"Found {len(general_results)} results for general search")
                                
                                for result in general_results:
                                    url = result.get('href', '')
                                    body = result.get('body', '')
                                    
                                    # Filter for relevant sources
                                    if url and body and any(domain in url.lower() for domain in 
                                           ['techcrunch', 'venturebeat', 'pitchbook', 'cbinsights', 
                                            'a16z', 'sequoia', 'ycombinator', 'firstround', 'accel', 'bvp']):
                                        knowledge_item = {
                                            'title': result.get('title', ''),
                                            'url': url,
                                            'content': body,
                                            'source_type': 'vc_knowledge',
                                            'query': query,
                                        }
                                        all_knowledge.append(knowledge_item)
                            except Exception as e:
                                self.logger.warning(f"General search failed for '{query}': {e}")
                            
                            time.sleep(1)  # Rate limiting
                            
                        except Exception as e:
                            self.logger.warning(f"Search failed for query '{query}': {e}")
                            continue
                
                self.logger.info(f"Collected {len(all_knowledge)} VC knowledge items from DuckDuckGo")
                
            except Exception as e:
                self.logger.error(f"VC knowledge search failed: {e}")
                import traceback
                self.logger.debug(traceback.format_exc())
        else:
            self.logger.warning("DuckDuckGo not available - install with: pip install duckduckgo-search")
        
        # Fallback: If no results from search, try direct scraping of known VC blogs
        if len(all_knowledge) == 0:
            self.logger.info("No results from search, trying fallback: direct scraping of known VC blogs...")
            all_knowledge = self._scrape_known_vc_blogs_fallback()
        
        return all_knowledge
    
    def _scrape_known_vc_blogs_fallback(self, max_urls: int = 10) -> List[Dict]:
        """
        Fallback method: Directly scrape known VC blog URLs if search fails
        
        Args:
            max_urls: Maximum number of URLs to try
            
        Returns:
            List of knowledge items
        """
        knowledge_items = []
        
        # Known VC blog URLs to try
        known_vc_urls = [
            'https://a16z.com/',
            'https://www.sequoiacap.com/',
            'https://firstround.com/review/',
            'https://avc.com/',
            'https://blog.ycombinator.com/',
            'https://www.greylock.com/',
            'https://www.bvp.com/',
        ]
        
        self.logger.info(f"Attempting to scrape {min(max_urls, len(known_vc_urls))} known VC blog URLs...")
        
        for url in known_vc_urls[:max_urls]:
            try:
                scraped = self.scrape_vc_blog(url)
                if scraped:
                    scraped['source_type'] = 'vc_blog_fallback'
                    knowledge_items.append(scraped)
                    self.logger.info(f"✅ Successfully scraped fallback URL: {url}")
                else:
                    self.logger.debug(f"Could not scrape: {url}")
                time.sleep(2)  # Be respectful with rate limiting
            except Exception as e:
                self.logger.warning(f"Failed to scrape {url}: {e}")
                continue
        
        self.logger.info(f"Fallback scraping collected {len(knowledge_items)} items")
        return knowledge_items
    
    def scrape_vc_blog(self, url: str) -> Optional[Dict]:
        """
        Scrape content from a VC blog or website
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict with title, content, and metadata
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
            
            # Extract title
            title = ''
            if soup.title:
                title = soup.title.string.strip()
            elif soup.find('h1'):
                title = soup.find('h1').get_text().strip()
            
            # Extract main content
            # Try common content containers
            content_selectors = [
                'article',
                'main',
                '.content',
                '.post-content',
                '.entry-content',
                '#content',
            ]
            
            content = ''
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator='\n', strip=True)
                    break
            
            # If no content found, get body text
            if not content:
                content = soup.get_text(separator='\n', strip=True)
            
            # Limit content length
            content = content[:10000]  # First 10k chars
            
            if content and len(content) > 200:  # Only return if substantial content
                return {
                    'title': title,
                    'url': url,
                    'content': content,
                    'source_type': 'vc_blog_scraped',
                }
            
        except Exception as e:
            self.logger.warning(f"Failed to scrape {url}: {e}")
        
        return None
    
    def collect_vc_knowledge_base(
        self, 
        max_items: int = 100, 
        custom_urls: Optional[List[str]] = None,
        scrape_custom_urls: bool = True
    ) -> List[Dict]:
        """
        Collect comprehensive VC knowledge base
        
        Args:
            max_items: Maximum items to collect
            custom_urls: Optional list of custom URLs/websites to scrape
            scrape_custom_urls: If True, scrape the custom URLs provided
            
        Returns:
            List of knowledge items
        """
        all_knowledge = []
        
        # Step 1: Search for VC knowledge (automatic research)
        self.logger.info("Step 1: Searching for VC knowledge...")
        search_results = self.search_vc_knowledge()
        self.logger.info(f"Search returned {len(search_results)} items")
        all_knowledge.extend(search_results)
        
        # If search returned very few results, try additional fallback
        if len(search_results) < 5:
            self.logger.info("Search returned few results, trying additional fallback methods...")
            # Try scraping a few more known VC blog URLs
            additional_items = self._scrape_known_vc_blogs_fallback(max_urls=5)
            all_knowledge.extend(additional_items)
            self.logger.info(f"Additional fallback collected {len(additional_items)} items")
        
        # Step 2: Scrape user-specified URLs/websites
        if custom_urls and scrape_custom_urls:
            self.logger.info(f"Scraping {len(custom_urls)} user-specified URLs...")
            for url in custom_urls:
                try:
                    scraped_content = self.scrape_vc_blog(url)
                    if scraped_content:
                        scraped_content['source_type'] = 'user_specified'
                        all_knowledge.append(scraped_content)
                        self.logger.info(f"✅ Successfully scraped: {url}")
                    else:
                        self.logger.warning(f"⚠️ Could not scrape: {url}")
                except Exception as e:
                    self.logger.error(f"❌ Error scraping {url}: {e}")
                    continue
        
        # Step 3: Scrape known VC blogs (optional, can be slow)
        # This can be done separately or on-demand
        
        # Deduplicate by URL
        seen_urls = set()
        unique_knowledge = []
        for item in all_knowledge:
            url = item.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_knowledge.append(item)
            
            if len(unique_knowledge) >= max_items:
                break
        
        self.logger.info(f"Collected {len(unique_knowledge)} unique VC knowledge items")
        
        return unique_knowledge
