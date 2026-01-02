"""
Company Research Agent
Performs internet research on companies and returns structured information
"""
import logging
import json
from typing import Dict, Optional, List
import requests
from bs4 import BeautifulSoup
from config import Config

# Try to import DuckDuckGo search (optional)
try:
    from duckduckgo_search import DDGS
    DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    try:
        import openai
        OPENAI_AVAILABLE = True
    except ImportError:
        OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class CompanyResearchAgent:
    """Agent that performs internet research on companies"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logger
        self.openai_key = config.get_openai_key() if OPENAI_AVAILABLE else None
        
    def research_company(
        self, 
        company_name: str,
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """
        Research a company and return structured information
        
        Args:
            company_name: Name of the company to research
            additional_info: Optional dict with additional info (industry, description, etc.)
            
        Returns:
            Dict with research findings:
            - company_name
            - country_of_incorporation
            - industry
            - industry_background (200 words)
            - company_background
            - founder_profile
            - competition
        """
        self.logger.info(f"Researching company: {company_name}")
        
        # Step 1: Search for company information
        search_results = self._search_company(company_name, additional_info)
        
        # Step 2: Extract and synthesize information
        research_data = self._synthesize_research(company_name, search_results, additional_info)
        
        return research_data
    
    def _search_company(self, company_name: str, additional_info: Optional[Dict] = None) -> List[Dict]:
        """Search for company information using DuckDuckGo or web scraping"""
        search_results = []
        
        # Build search queries
        queries = [
            f"{company_name} company information",
            f"{company_name} founders",
            f"{company_name} location country",
        ]
        
        # Add industry-specific query if available
        if additional_info and additional_info.get('industry'):
            queries.append(f"{company_name} {additional_info['industry']} industry")
        
        # Try DuckDuckGo search first (free, no API key)
        if DDG_AVAILABLE:
            try:
                self.logger.info("Using DuckDuckGo search")
                with DDGS() as ddgs:
                    for query in queries[:3]:  # Limit to 3 queries
                        try:
                            results = list(ddgs.text(query, max_results=3))
                            search_results.extend(results)
                        except Exception as e:
                            self.logger.warning(f"DuckDuckGo search failed for '{query}': {e}")
                self.logger.info(f"Found {len(search_results)} search results")
            except Exception as e:
                self.logger.warning(f"DuckDuckGo not available: {e}")
        
        # Fallback: Try to scrape company website if available in additional_info
        if additional_info and additional_info.get('website'):
            try:
                website_content = self._scrape_website(additional_info['website'])
                if website_content:
                    search_results.append({
                        'title': f"{company_name} - Official Website",
                        'body': website_content,
                        'href': additional_info['website']
                    })
            except Exception as e:
                self.logger.warning(f"Failed to scrape website: {e}")
        
        return search_results
    
    def _scrape_website(self, url: str) -> Optional[str]:
        """Scrape text content from a website"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            # Extract text
            text = soup.get_text(separator='\n', strip=True)
            # Limit text length
            return text[:5000]  # First 5000 chars
        except Exception as e:
            self.logger.warning(f"Failed to scrape {url}: {e}")
            return None
    
    def _synthesize_research(
        self, 
        company_name: str, 
        search_results: List[Dict],
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """Synthesize search results into structured research data"""
        
        # If OpenAI is available, use it to synthesize
        if self.openai_key and OPENAI_AVAILABLE:
            return self._synthesize_with_openai(company_name, search_results, additional_info)
        else:
            # Fallback: Basic extraction from search results
            return self._synthesize_basic(company_name, search_results, additional_info)
    
    def _synthesize_with_openai(
        self,
        company_name: str,
        search_results: List[Dict],
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """Use OpenAI to synthesize research into structured format"""
        
        # Prepare context from search results
        context = ""
        for i, result in enumerate(search_results[:5], 1):  # Use top 5 results
            title = result.get('title', '')
            body = result.get('body', '')[:1000]  # Limit body length
            href = result.get('href', '')
            context += f"\n\nSource {i}:\nTitle: {title}\nURL: {href}\nContent: {body}\n"
        
        # Add additional info if available
        additional_context = ""
        if additional_info:
            if additional_info.get('industry'):
                additional_context += f"\nKnown industry: {additional_info['industry']}"
            if additional_info.get('description'):
                additional_context += f"\nKnown description: {additional_info['description']}"
        
        prompt = f"""You are a research analyst. Research the company "{company_name}" based on the following search results and provide a structured research summary.

{additional_context}

Search Results:
{context}

Please provide a comprehensive research summary in the following JSON format:
{{
    "company_name": "{company_name}",
    "country_of_incorporation": "Country name or 'Unknown' if not found",
    "industry": "Primary industry the company operates in",
    "industry_background": "A comprehensive 200-word overview of the industry, its current state, trends, and growth prospects for the next few years",
    "company_background": "Detailed background about the company including history, business model, products/services, and key milestones",
    "founder_profile": "Information about the founder(s) including names, background, experience, and notable achievements",
    "competition": "Overview of main competitors and competitive landscape in the sector"
}}

Important:
- The industry_background should be approximately 200 words
- Be specific and factual based on the search results
- If information is not available, use "Not available" or "Unknown"
- Cite sources when possible (from the URLs provided)

Return ONLY valid JSON, no additional text."""

        try:
            # Use OpenAI client (new API) if available, otherwise fallback to old API
            try:
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional research analyst. Always return valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                response_text = response.choices[0].message.content.strip()
            except (NameError, AttributeError):
                # Fallback to old OpenAI API
                import openai
                openai.api_key = self.openai_key
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional research analyst. Always return valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2000
                )
                response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            research_data = json.loads(response_text)
            
            # Validate required fields
            required_fields = [
                'company_name', 'country_of_incorporation', 'industry',
                'industry_background', 'company_background', 'founder_profile', 'competition'
            ]
            for field in required_fields:
                if field not in research_data:
                    research_data[field] = "Not available"
            
            return research_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse OpenAI JSON response: {e}")
            self.logger.error(f"Response was: {response_text[:500]}")
            return self._synthesize_basic(company_name, search_results, additional_info)
        except Exception as e:
            self.logger.error(f"OpenAI synthesis failed: {e}")
            return self._synthesize_basic(company_name, search_results, additional_info)
    
    def _synthesize_basic(
        self,
        company_name: str,
        search_results: List[Dict],
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """Basic synthesis without OpenAI (fallback)"""
        # Extract basic information from search results
        all_text = " ".join([r.get('body', '') for r in search_results[:3]])
        all_text = all_text[:3000]  # Limit length
        
        # Basic extraction (very simple)
        industry = additional_info.get('industry', 'Unknown') if additional_info else 'Unknown'
        
        return {
            "company_name": company_name,
            "country_of_incorporation": "Unknown",
            "industry": industry,
            "industry_background": f"Industry information for {industry} is not available in this basic mode. Please install OpenAI API key for detailed research.",
            "company_background": all_text[:500] if all_text else "Company background not available.",
            "founder_profile": "Founder information not available in basic mode.",
            "competition": "Competitive information not available in basic mode."
        }
