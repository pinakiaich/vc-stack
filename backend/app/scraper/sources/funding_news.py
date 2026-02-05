"""
Funding news aggregator
Scrapes funding announcements from news sources
"""
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
try:
    import feedparser
except ImportError:
    feedparser = None
from ..base import BaseScraper

logger = logging.getLogger(__name__)


class FundingNewsScraper(BaseScraper):
    """Scrape funding announcements from news feeds"""
    
    TECHCRUNCH_RSS = "https://techcrunch.com/tag/funding/feed/"
    NEWSAPI_BASE = "https://newsapi.org/v2/everything"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.newsapi_key = config.get("newsapi_key")  # Optional API key
    
    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape funding news"""
        companies = []
        
        try:
            # Scrape TechCrunch RSS
            tc_companies = self._scrape_techcrunch()
            companies.extend(tc_companies)
            
            # Scrape NewsAPI if key is available
            if self.newsapi_key:
                newsapi_companies = self._scrape_newsapi()
                companies.extend(newsapi_companies)
            
            logger.info(f"Scraped {len(companies)} companies from funding news")
        except Exception as e:
            logger.error(f"Error scraping funding news: {e}")
        
        return companies
    
    def _scrape_techcrunch(self) -> List[Dict[str, Any]]:
        """Scrape TechCrunch RSS feed"""
        companies = []
        
        if not feedparser:
            logger.warning("feedparser not installed - skipping TechCrunch RSS")
            return companies
        
        try:
            feed = feedparser.parse(self.TECHCRUNCH_RSS)
            
            for entry in feed.entries[:50]:  # Limit to recent 50
                # Only process entries from last 30 days
                published = datetime(*entry.published_parsed[:6])
                if (datetime.now() - published).days > 30:
                    continue
                
                company = self._parse_funding_article(entry)
                if company:
                    companies.append(company)
                    
        except Exception as e:
            logger.error(f"Error scraping TechCrunch: {e}")
        
        return companies
    
    def _scrape_newsapi(self) -> List[Dict[str, Any]]:
        """Scrape NewsAPI for funding news"""
        companies = []
        
        if not self.newsapi_key:
            return companies
        
        try:
            # Search for funding-related articles
            query = "startup funding series B series C"
            url = f"{self.NEWSAPI_BASE}?q={query}&apiKey={self.newsapi_key}&sortBy=publishedAt&language=en"
            
            response = self._fetch(url)
            data = response.json()
            
            for article in data.get("articles", [])[:20]:  # Limit to 20
                company = self._parse_newsapi_article(article)
                if company:
                    companies.append(company)
                    
        except Exception as e:
            logger.error(f"Error scraping NewsAPI: {e}")
        
        return companies
    
    def _parse_funding_article(self, entry: Any) -> Optional[Dict[str, Any]]:
        """Parse a funding article to extract company info"""
        try:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            
            # Extract company name (usually in title)
            company_name = self._extract_company_name(title, summary)
            if not company_name:
                return None
            
            # Extract funding amount and round
            funding_info = self._extract_funding_info(title + " " + summary)
            
            # Extract investors
            investors = self._extract_investors(summary)
            
            return {
                "name": company_name,
                "description": summary[:500] if summary else "",
                "stage": funding_info.get("stage", ""),
                "valuation": funding_info.get("valuation"),
                "key_investors": ", ".join(investors) if investors else "",
                "location": "United States",  # Default, could be enhanced
                "source": "techcrunch",
                "source_url": link,
                "raw_data": {
                    "title": title,
                    "summary": summary,
                    "link": link,
                },
            }
        except Exception as e:
            logger.error(f"Error parsing funding article: {e}")
            return None
    
    def _parse_newsapi_article(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse NewsAPI article"""
        try:
            title = article.get("title", "")
            description = article.get("description", "")
            content = article.get("content", "")
            url = article.get("url", "")
            
            company_name = self._extract_company_name(title, description)
            if not company_name:
                return None
            
            funding_info = self._extract_funding_info(title + " " + description + " " + content)
            investors = self._extract_investors(description + " " + content)
            
            return {
                "name": company_name,
                "description": description[:500] if description else "",
                "stage": funding_info.get("stage", ""),
                "valuation": funding_info.get("valuation"),
                "key_investors": ", ".join(investors) if investors else "",
                "location": "United States",
                "source": "newsapi",
                "source_url": url,
                "raw_data": article,
            }
        except Exception as e:
            logger.error(f"Error parsing NewsAPI article: {e}")
            return None
    
    def _extract_company_name(self, title: str, text: str) -> Optional[str]:
        """Extract company name from title/text"""
        # Simple pattern: "CompanyName raises $X" or "CompanyName secures funding"
        patterns = [
            r"^([A-Z][a-zA-Z0-9\s&]+?)\s+(?:raises|secures|closes|announces)",
            r"^([A-Z][a-zA-Z0-9\s&]+?)\s+\$",
            r"([A-Z][a-zA-Z0-9\s&]+?)\s+raises",
        ]
        
        combined = title + " " + text
        for pattern in patterns:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common false positives
                if name.lower() not in ["the", "a", "an", "this", "that"]:
                    return name
        
        return None
    
    def _extract_funding_info(self, text: str) -> Dict[str, Any]:
        """Extract funding amount, round type, and valuation"""
        info = {"stage": "", "valuation": None}
        
        # Extract round type
        stage_patterns = {
            "Series C": r"series\s+c|series\s+iii",
            "Series B": r"series\s+b|series\s+ii",
            "Series A": r"series\s+a|series\s+i",
            "Seed": r"seed\s+round",
        }
        
        text_lower = text.lower()
        for stage, pattern in stage_patterns.items():
            if re.search(pattern, text_lower):
                info["stage"] = stage
                break
        
        # Extract valuation (e.g., "$100M", "$500 million")
        valuation_patterns = [
            r"\$(\d+(?:\.\d+)?)\s*(?:million|m|billion|b)\s+(?:valuation|valued)",
            r"valued\s+at\s+\$(\d+(?:\.\d+)?)\s*(?:million|m|billion|b)",
        ]
        
        for pattern in valuation_patterns:
            match = re.search(pattern, text_lower)
            if match:
                amount = float(match.group(1))
                if "billion" in text_lower or "b" in text_lower:
                    amount *= 1_000_000_000
                elif "million" in text_lower or "m" in text_lower:
                    amount *= 1_000_000
                info["valuation"] = int(amount)
                break
        
        return info
    
    def _extract_investors(self, text: str) -> List[str]:
        """Extract investor names from text"""
        investors = []
        
        # Common investor patterns
        investor_keywords = [
            "led by",
            "led the",
            "investors include",
            "backed by",
            "participated by",
        ]
        
        text_lower = text.lower()
        for keyword in investor_keywords:
            if keyword in text_lower:
                # Extract text after keyword
                idx = text_lower.find(keyword)
                snippet = text[idx:idx+200]  # Next 200 chars
                
                # Look for known VC names (simplified - could be enhanced)
                known_vcs = [
                    "sequoia", "a16z", "andreessen horowitz", "accel", "greylock",
                    "kleiner perkins", "benchmark", "insight partners", "tiger global",
                ]
                
                for vc in known_vcs:
                    if vc in snippet.lower():
                        investors.append(vc.title())
        
        return list(set(investors))  # Remove duplicates
