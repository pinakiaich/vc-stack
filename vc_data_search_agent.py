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
                with DDGS() as ddgs:
                    for query in search_queries:
                        try:
                            # Search for VC knowledge
                            results = list(ddgs.text(
                                f"{query} site:a16z.com OR site:sequoiacap.com OR site:firstround.com OR site:avc.com",
                                max_results=5
                            ))
                            
                            for result in results:
                                knowledge_item = {
                                    'title': result.get('title', ''),
                                    'url': result.get('href', ''),
                                    'content': result.get('body', ''),
                                    'source_type': 'vc_blog',
                                    'query': query,
                                }
                                all_knowledge.append(knowledge_item)
                            
                            # Also search general VC knowledge
                            general_results = list(ddgs.text(
                                query,
                                max_results=5
                            ))
                            
                            for result in general_results:
                                url = result.get('href', '')
                                # Filter for relevant sources
                                if any(domain in url.lower() for domain in 
                                       ['techcrunch', 'venturebeat', 'pitchbook', 'cbinsights', 
                                        'a16z', 'sequoia', 'ycombinator', 'firstround']):
                                    knowledge_item = {
                                        'title': result.get('title', ''),
                                        'url': url,
                                        'content': result.get('body', ''),
                                        'source_type': 'vc_knowledge',
                                        'query': query,
                                    }
                                    all_knowledge.append(knowledge_item)
                            
                            time.sleep(1)  # Rate limiting
                            
                        except Exception as e:
                            self.logger.warning(f"Search failed for query '{query}': {e}")
                            continue
                
                self.logger.info(f"Collected {len(all_knowledge)} VC knowledge items")
                
            except Exception as e:
                self.logger.error(f"VC knowledge search failed: {e}")
        else:
            self.logger.warning("DuckDuckGo not available - install with: pip install duckduckgo-search")
        
        return all_knowledge
    
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
    
    def collect_vc_knowledge_base(self, max_items: int = 100) -> List[Dict]:
        """
        Collect comprehensive VC knowledge base
        
        Args:
            max_items: Maximum items to collect
            
        Returns:
            List of knowledge items
        """
        all_knowledge = []
        
        # Step 1: Search for VC knowledge
        self.logger.info("Searching for VC knowledge...")
        search_results = self.search_vc_knowledge()
        all_knowledge.extend(search_results)
        
        # Step 2: Scrape known VC blogs (optional, can be slow)
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
