"""
Open datasets scraper
Uses publicly available startup datasets
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import httpx

from ..base import BaseScraper

logger = logging.getLogger(__name__)

# Local fixture used when remote URL fails (e.g. 404, rate limit)
_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "yc_sample.json"

# Y Combinator companies list (public JSON); may 404 if repo moved
YC_COMPANIES_URL = "https://raw.githubusercontent.com/ankitvadari/ycombinator-companies/main/companies.json"


class OpenDataScraper(BaseScraper):
    """Scrape from open/public datasets"""

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrape from open datasets"""
        companies: List[Dict[str, Any]] = []

        try:
            yc_companies = self._fetch_yc_companies()
            companies.extend(yc_companies)
            logger.info("Scraped %d companies from open datasets", len(companies))
        except Exception as e:
            logger.error("Error scraping open data: %s", e)

        return companies

    def _fetch_yc_companies(self) -> List[Dict[str, Any]]:
        """Fetch YC companies from remote URL or local fixture fallback."""
        companies: List[Dict[str, Any]] = []

        try:
            response = self._fetch(YC_COMPANIES_URL)
            data = response.json()
            logger.info("Fetched %d items from remote URL", len(data) if isinstance(data, list) else 0)
            for item in data:
                company = self._parse_yc_company(item)
                if company:
                    companies.append(company)
            if companies:
                logger.info("Successfully parsed %d companies from remote", len(companies))
                return companies
        except Exception as e:
            logger.warning("Remote YC dataset failed (%s), using local fixture", e)

        try:
            with open(_FIXTURE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Loaded fixture with %d items", len(data) if isinstance(data, list) else 0)
            for item in data:
                company = self._parse_yc_company(item)
                if company:
                    companies.append(company)
            logger.info("Loaded %d companies from fixture %s", len(companies), _FIXTURE_PATH)
        except Exception as e:
            logger.error("Error loading YC fixture: %s", e, exc_info=True)

        return companies
    
    def _parse_yc_company(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse YC company data and try to extract additional info"""
        try:
            # Extract basic info
            name = data.get("name", "").strip()
            if not name:
                return None
            
            description = data.get("description", "").strip()
            website = data.get("website", "").strip()
            batch = data.get("batch", "")
            industry = data.get("industry", "").strip()
            
            # Try to extract valuation/funding info from description or other fields
            valuation = None
            key_investors = None
            stage = ""
            
            # Look for funding info in description
            desc_lower = description.lower() if description else ""
            if "series b" in desc_lower or "series ii" in desc_lower:
                stage = "Series B"
            elif "series c" in desc_lower or "series iii" in desc_lower:
                stage = "Series C"
            elif "series a" in desc_lower:
                stage = "Series A"
            
            # Try to extract valuation from description (e.g., "raised $50M", "valued at $100M")
            import re
            if description:
                # Look for patterns like "$50M", "$100 million", "valued at $200M"
                valuation_match = re.search(r'(?:valued at|valuation|raised)\s*\$?(\d+(?:\.\d+)?)\s*(million|m|billion|b)', desc_lower)
                if valuation_match:
                    amount = float(valuation_match.group(1))
                    unit = valuation_match.group(2).lower()
                    if 'b' in unit or 'billion' in unit:
                        valuation = amount * 1_000_000_000
                    else:
                        valuation = amount * 1_000_000
            
            # Look for investors in description
            investor_keywords = ["backed by", "investors include", "funded by", "led by"]
            for keyword in investor_keywords:
                if keyword in desc_lower:
                    # Try to extract investor names (simplified - could be enhanced)
                    parts = description.split(keyword, 1)
                    if len(parts) > 1:
                        potential_investors = parts[1].split('.')[0].strip()
                        if len(potential_investors) < 100:  # Reasonable length
                            key_investors = potential_investors
            
            return {
                "name": name,
                "description": description,
                "industry": industry,
                "stage": stage,
                "valuation": valuation,
                "key_investors": key_investors,
                "website": website,
                "location": "United States",  # Most YC companies are US-based
                "batch": batch,
                "source": "yc",
                "raw_data": data,
            }
        except Exception as e:
            logger.error(f"Error parsing YC company: {e}")
            return None
