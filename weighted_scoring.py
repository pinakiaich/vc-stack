"""
Multi-Field Weighted Scoring System
Provides structured scoring based on different field weights
"""
import logging
from typing import Dict, List, Optional, Any
import re


class WeightedScoring:
    """
    Multi-field weighted scoring system for more accurate ranking
    """
    
    # Default field weights (can be customized per VC firm)
    DEFAULT_WEIGHTS = {
        'revenue': 0.25,
        'stage': 0.20,
        'investors': 0.20,
        'industry': 0.15,
        'description': 0.10,
        'location': 0.10
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize weighted scoring
        
        Args:
            weights: Custom field weights. If None, uses DEFAULT_WEIGHTS
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.logger = logging.getLogger(__name__)
        
        # Validate weights sum to ~1.0
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            self.logger.warning(f"Field weights sum to {total}, not 1.0. Normalizing...")
            self.weights = {k: v/total for k, v in self.weights.items()}
    
    def calculate_field_score(
        self, 
        firm: Dict, 
        criteria: str, 
        field: str
    ) -> float:
        """
        Calculate score for a specific field
        
        Args:
            firm: Firm dictionary
            criteria: Investment criteria text
            field: Field name to score
            
        Returns:
            Score between 0.0 and 1.0
        """
        field_value = str(firm.get(field, '')).lower().strip()
        criteria_lower = criteria.lower()
        
        if not field_value or field_value == 'nan':
            return 0.0
        
        # Field-specific scoring logic
        if field == 'revenue':
            return self._score_revenue(firm, criteria)
        elif field == 'stage':
            return self._score_stage(firm, criteria)
        elif field == 'investors':
            return self._score_investors(firm, criteria)
        elif field == 'industry':
            return self._score_industry(firm, criteria)
        elif field == 'description':
            return self._score_description(firm, criteria)
        elif field == 'location':
            return self._score_location(firm, criteria)
        else:
            # Generic keyword matching
            keywords = self._extract_keywords(criteria_lower)
            matches = sum(1 for kw in keywords if kw in field_value)
            return min(matches / max(len(keywords), 1), 1.0)
    
    def calculate_composite_score(
        self, 
        firm: Dict, 
        criteria: str,
        vector_similarity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate composite weighted score for a firm
        
        Args:
            firm: Firm dictionary
            criteria: Investment criteria
            vector_similarity: Optional vector similarity score (0-1)
            
        Returns:
            Dictionary with scores and breakdown
        """
        field_scores = {}
        
        # Calculate score for each weighted field
        for field, weight in self.weights.items():
            field_scores[field] = self.calculate_field_score(firm, criteria, field)
        
        # Calculate weighted average
        composite_score = sum(
            field_scores[field] * weight 
            for field, weight in self.weights.items()
        )
        
        # Optionally combine with vector similarity
        if vector_similarity is not None:
            # Weighted combination: 60% field scores, 40% vector similarity
            composite_score = 0.6 * composite_score + 0.4 * vector_similarity
        
        return {
            'composite_score': composite_score,
            'field_scores': field_scores,
            'vector_similarity': vector_similarity
        }
    
    def _score_revenue(self, firm: Dict, criteria: str) -> float:
        """Score revenue field based on criteria"""
        revenue_str = str(firm.get('revenue', '')).lower()
        criteria_lower = criteria.lower()
        
        # Extract revenue numbers from criteria (e.g., "$5M", "5 million")
        revenue_thresholds = self._extract_revenue_numbers(criteria_lower)
        
        if not revenue_thresholds:
            # No specific revenue requirement
            if 'pre-revenue' in revenue_str or 'no revenue' in revenue_str:
                return 0.3  # Low score for pre-revenue if revenue not specified
            return 0.7  # Neutral score
        
        # Extract firm revenue
        firm_revenue = self._extract_revenue_amount(revenue_str)
        
        if firm_revenue is None:
            return 0.0  # No revenue data
        
        # Check if firm revenue meets thresholds
        min_threshold = min(revenue_thresholds)
        max_threshold = max(revenue_thresholds) if len(revenue_thresholds) > 1 else float('inf')
        
        if min_threshold <= firm_revenue <= max_threshold:
            return 1.0  # Perfect match
        elif firm_revenue > min_threshold * 0.8:
            return 0.8  # Close match
        elif firm_revenue > min_threshold * 0.5:
            return 0.5  # Partial match
        else:
            return 0.2  # Below threshold
    
    def _score_stage(self, firm: Dict, criteria: str) -> float:
        """Score funding stage"""
        stage = str(firm.get('stage', '')).lower()
        criteria_lower = criteria.lower()
        
        # Common stage keywords
        stages = ['pre-seed', 'seed', 'series a', 'series b', 'series c', 'series d', 'growth']
        
        # Extract mentioned stages from criteria
        mentioned_stages = [s for s in stages if s in criteria_lower]
        
        if not mentioned_stages:
            return 0.7  # Neutral if no stage specified
        
        # Check if firm stage matches
        for mentioned in mentioned_stages:
            if mentioned in stage:
                return 1.0  # Exact match
        
        return 0.3  # No match
    
    def _score_investors(self, firm: Dict, criteria: str) -> float:
        """Score investor quality"""
        investors = str(firm.get('Active Investors', firm.get('investors', ''))).lower()
        criteria_lower = criteria.lower()
        
        if not investors or investors == 'nan':
            return 0.3  # Low score if no investor data
        
        # Check for tier-1 investor mentions
        tier1_keywords = ['sequoia', 'andreessen', 'accel', 'greylock', 'benchmark', 
                         'kleiner', 'lightspeed', 'bessemer', 'insight']
        
        has_tier1 = any(kw in investors for kw in tier1_keywords)
        
        if 'top-tier' in criteria_lower or 'tier-1' in criteria_lower:
            return 1.0 if has_tier1 else 0.3
        
        # General investor quality
        return 0.8 if has_tier1 else 0.5
    
    def _score_industry(self, firm: Dict, criteria: str) -> float:
        """Score industry match"""
        industry = str(firm.get('industry', '')).lower()
        criteria_lower = criteria.lower()
        
        if not industry or industry == 'nan':
            return 0.3
        
        # Extract keywords from criteria
        keywords = self._extract_keywords(criteria_lower)
        
        # Check for matches
        matches = sum(1 for kw in keywords if kw in industry and len(kw) > 3)
        
        if matches > 0:
            return min(matches / 3.0, 1.0)  # Cap at 1.0
        
        return 0.3
    
    def _score_description(self, firm: Dict, criteria: str) -> float:
        """Score description relevance"""
        description = str(firm.get('description', '')).lower()
        criteria_lower = criteria.lower()
        
        if not description or len(description) < 10:
            return 0.2
        
        keywords = self._extract_keywords(criteria_lower)
        matches = sum(1 for kw in keywords if kw in description and len(kw) > 3)
        
        return min(matches / max(len(keywords), 1), 1.0)
    
    def _score_location(self, firm: Dict, criteria: str) -> float:
        """Score location match"""
        location = str(firm.get('location', '')).lower()
        criteria_lower = criteria.lower()
        
        if not location or location == 'nan':
            return 0.5  # Neutral if no location specified
        
        # Extract location keywords
        location_keywords = ['san francisco', 'sf', 'bay area', 'new york', 'nyc', 
                           'boston', 'seattle', 'austin', 'europe', 'london', 'berlin']
        
        mentioned_locations = [loc for loc in location_keywords if loc in criteria_lower]
        
        if not mentioned_locations:
            return 0.7  # Neutral if location not specified
        
        for loc in mentioned_locations:
            if loc in location:
                return 1.0
        
        return 0.3
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common stop words and short words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                     'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        return list(set(keywords))  # Remove duplicates
    
    def _extract_revenue_numbers(self, text: str) -> List[float]:
        """Extract revenue thresholds from criteria text"""
        # Pattern: $5M, 5 million, $10M+, etc.
        patterns = [
            r'\$(\d+(?:\.\d+)?)\s*[Mm]',  # $5M, $10.5M
            r'(\d+(?:\.\d+)?)\s*million',  # 5 million
            r'revenue.*?(\d+(?:\.\d+)?)\s*[Mm]',  # revenue > $5M
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                num = float(match)
                # Convert to base number (assume M = million)
                numbers.append(num * 1_000_000)
        
        return numbers
    
    def _extract_revenue_amount(self, revenue_str: str) -> Optional[float]:
        """Extract revenue amount from firm revenue string"""
        if not revenue_str or revenue_str == 'nan':
            return None
        
        # Try to extract number
        match = re.search(r'(\d+(?:\.\d+)?)', revenue_str)
        if not match:
            return None
        
        num = float(match.group(1))
        
        # Determine multiplier (M = million, K = thousand, B = billion)
        if 'b' in revenue_str or 'billion' in revenue_str:
            return num * 1_000_000_000
        elif 'm' in revenue_str or 'million' in revenue_str:
            return num * 1_000_000
        elif 'k' in revenue_str or 'thousand' in revenue_str:
            return num * 1_000
        else:
            # Assume millions if no unit
            return num * 1_000_000
