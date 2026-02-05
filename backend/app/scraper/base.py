"""
Base scraper class with common functionality
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import httpx

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all scrapers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limit_delay = config.get("rate_limit_delay", 1.0)
        self.max_retries = config.get("max_retries", 3)
        self.timeout = config.get("timeout_seconds", 30)
        self.user_agent = config.get("user_agent", "Mozilla/5.0")
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        """Fetch URL with retry logic"""
        self._rate_limit()
        
        default_headers = {"User-Agent": self.user_agent}
        if headers:
            default_headers.update(headers)
        
        try:
            response = httpx.get(url, headers=default_headers, timeout=self.timeout, follow_redirects=True)
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise
    
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method - must be implemented by subclasses
        
        Returns:
            List of company dictionaries matching FirmData schema
        """
        pass
    
    def normalize_company_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize scraped data to standard format
        
        Args:
            raw_data: Raw scraped data
            
        Returns:
            Normalized company data
        """
        return {
            "name": raw_data.get("name", "").strip(),
            "description": raw_data.get("description", "").strip(),
            "industry": raw_data.get("industry", "").strip(),
            "stage": raw_data.get("stage", "").strip(),
            "revenue": raw_data.get("revenue", "").strip(),
            "location": raw_data.get("location", "").strip(),
            "valuation": raw_data.get("valuation"),
            "key_investors": raw_data.get("key_investors", "").strip(),
            "raw_data": raw_data,
        }
