"""
Data validator for scraped companies
Applies filter criteria, deduplicates, and normalizes data
"""
import logging
import re
from typing import List, Dict, Any, Optional, Set
from .config import COMPANY_FILTERS

logger = logging.getLogger(__name__)


class CompanyValidator:
    """Validate and filter scraped company data"""
    
    def __init__(self, filters: Optional[Dict[str, Any]] = None):
        self.filters = filters or COMPANY_FILTERS
        self.seen_companies: Set[str] = set()  # For deduplication
    
    def validate(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and filter companies
        
        Args:
            companies: List of raw company data
            
        Returns:
            List of validated companies matching filter criteria
        """
        validated = []
        
        for idx, company in enumerate(companies):
            company_name = company.get("name", f"Company #{idx+1}")
            logger.debug(f"Validating company {idx+1}/{len(companies)}: {company_name}")
            
            # Normalize first
            normalized = self.normalize(company)
            if not normalized:
                logger.debug(f"  ✗ Skipped: normalization failed for {company_name}")
                continue
            
            # Check if duplicate
            if self._is_duplicate(normalized):
                logger.debug(f"  ✗ Skipped: duplicate {company_name}")
                continue
            
            # Apply filters and generate reasoning
            match_result, reasoning = self._matches_filters_with_reasoning(normalized)
            if match_result:
                normalized['match_reasoning'] = reasoning
                validated.append(normalized)
                # Track for deduplication
                self._add_to_seen(normalized)
                logger.debug(f"  ✓ Passed: {company_name} - {reasoning}")
            else:
                logger.debug(f"  ✗ Filtered out: {company_name} (didn't match filter criteria)")
        
        logger.info(f"Validated {len(validated)}/{len(companies)} companies")
        return validated
    
    def normalize(self, company: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize company data"""
        try:
            name = self._normalize_name(company.get("name", ""))
            if not name:
                return None
            
            normalized = {
                "name": name,
                "description": self._normalize_text(company.get("description", "")),
                "industry": self._normalize_text(company.get("industry", "")),
                "stage": self._normalize_stage(company.get("stage", "")),
                "revenue": self._normalize_text(company.get("revenue", "")),
                "location": self._normalize_location(company.get("location", "")),
                "valuation": self._normalize_valuation(company.get("valuation")),
                "key_investors": self._normalize_text(company.get("key_investors", "")),
                "website": company.get("website", "").strip(),
                "linkedin_url": company.get("linkedin_url", "").strip(),
                "raw_data": company,
            }
            
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing company {company.get('name')}: {e}")
            return None
    
    def _normalize_name(self, name: str) -> str:
        """Normalize company name"""
        if not name:
            return ""
        
        name = name.strip()
        # Remove common suffixes
        name = re.sub(r'\s+(Inc\.?|LLC|Ltd\.?|Corp\.?)$', '', name, flags=re.IGNORECASE)
        return name
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text fields"""
        if not text:
            return ""
        return text.strip()
    
    def _normalize_stage(self, stage: str) -> str:
        """Normalize funding stage"""
        if not stage:
            return ""
        
        stage = stage.strip()
        stage_lower = stage.lower()
        
        # Map variations to standard names
        stage_map = {
            "series b": "Series B",
            "series ii": "Series B",
            "series 2": "Series B",
            "series c": "Series C",
            "series iii": "Series C",
            "series 3": "Series C",
        }
        
        for key, value in stage_map.items():
            if key in stage_lower:
                return value
        
        # If it already matches, return as-is
        if stage in ["Series B", "Series C"]:
            return stage
        
        return stage
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location"""
        if not location:
            return ""
        
        location = location.strip()
        location_lower = location.lower()
        
        # Normalize US location variations
        us_variations = ["united states", "usa", "us", "u.s.", "u.s.a."]
        for variation in us_variations:
            if variation in location_lower:
                return "United States"
        
        return location
    
    def _normalize_valuation(self, valuation: Any) -> Optional[float]:
        """Normalize valuation to USD float"""
        if valuation is None:
            return None
        
        if isinstance(valuation, (int, float)):
            return float(valuation)
        
        if isinstance(valuation, str):
            # Extract number from string like "$100M", "500 million"
            match = re.search(r'(\d+(?:\.\d+)?)', valuation.replace(',', ''))
            if match:
                amount = float(match.group(1))
                # Check for multiplier
                if 'billion' in valuation.lower() or 'b' in valuation.lower():
                    amount *= 1_000_000_000
                elif 'million' in valuation.lower() or 'm' in valuation.lower():
                    amount *= 1_000_000
                return amount
        
        return None
    
    def _is_duplicate(self, company: Dict[str, Any]) -> bool:
        """Check if company is a duplicate"""
        name = company.get("name", "").lower().strip()
        website = company.get("website", "").lower().strip()
        
        # Check by name
        if name in self.seen_companies:
            return True
        
        # Check by domain (if website provided)
        if website:
            try:
                from urllib.parse import urlparse
                domain = urlparse(website).netloc
                if domain and domain in self.seen_companies:
                    return True
            except:
                pass
        
        return False
    
    def _add_to_seen(self, company: Dict[str, Any]):
        """Add company to seen set"""
        name = company.get("name", "").lower().strip()
        if name:
            self.seen_companies.add(name)
        
        website = company.get("website", "").lower().strip()
        if website:
            try:
                from urllib.parse import urlparse
                domain = urlparse(website).netloc
                if domain:
                    self.seen_companies.add(domain)
            except:
                pass
    
    def _matches_filters(self, company: Dict[str, Any]) -> bool:
        """Check if company matches filter criteria (legacy method for compatibility)"""
        result, _ = self._matches_filters_with_reasoning(company)
        return result
    
    def _matches_filters_with_reasoning(self, company: Dict[str, Any]) -> tuple[bool, str]:
        """Check if company matches filter criteria and return reasoning"""
        reasons = []
        fails = []
        
        # Stage filter: only apply when company has a stage; missing stage = allow
        required_stages = self.filters.get("stage", [])
        if required_stages:
            company_stage = (company.get("stage") or "").strip()
            if company_stage:
                if company_stage in required_stages:
                    reasons.append(f"Stage: {company_stage}")
                else:
                    fails.append(f"Stage {company_stage} not in {required_stages}")
                    return False, ""
            else:
                reasons.append("Stage: Not specified (accepted)")
        
        # Valuation filter: only apply when company has valuation; missing = allow
        valuation_min = self.filters.get("valuation_min")
        valuation_max = self.filters.get("valuation_max")
        company_valuation = company.get("valuation")
        
        if company_valuation is not None and (valuation_min or valuation_max):
            if valuation_min and company_valuation < valuation_min:
                fails.append(f"Valuation ${company_valuation/1_000_000:.0f}M below minimum ${valuation_min/1_000_000:.0f}M")
                return False, ""
            if valuation_max and company_valuation > valuation_max:
                fails.append(f"Valuation ${company_valuation/1_000_000:.0f}M above maximum ${valuation_max/1_000_000:.0f}M")
                return False, ""
            if company_valuation:
                reasons.append(f"Valuation: ${company_valuation/1_000_000:.0f}M")
        elif company_valuation:
            reasons.append(f"Valuation: ${company_valuation/1_000_000:.0f}M")
        else:
            reasons.append("Valuation: Not specified (accepted)")
        
        # Location filter
        required_locations = self.filters.get("location", [])
        if required_locations:
            company_location = company.get("location", "")
            location_lower = company_location.lower()
            matches = any(
                req_loc.lower() in location_lower or location_lower in req_loc.lower()
                for req_loc in required_locations
            )
            if matches:
                reasons.append(f"Location: {company_location}")
            else:
                if company_location:
                    fails.append(f"Location {company_location} not in required locations")
                else:
                    fails.append("Location not specified")
                return False, ""
        elif company.get("location"):
            reasons.append(f"Location: {company.get('location')}")
        
        # Exclude industries
        exclude_industries = self.filters.get("exclude_industries", [])
        if exclude_industries:
            company_industry = company.get("industry", "").lower()
            for excluded in exclude_industries:
                if excluded.lower() in company_industry:
                    fails.append(f"Excluded industry: {excluded}")
                    return False, ""
        
        if company.get("industry"):
            reasons.append(f"Industry: {company.get('industry')}")
        
        # Build reasoning string
        if reasons:
            reasoning = " | ".join(reasons)
        else:
            reasoning = "Matches basic criteria (US location, not excluded)"
        
        return True, reasoning
