"""
Industry Hierarchy Agent
Understands hierarchical industry classifications (e.g., IT → Computer Hardware → GPUs)
"""
import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class IndustryHierarchyAgent:
    """Agent that understands and extracts hierarchical industry classifications"""
    
    def __init__(self):
        self.logger = logger
        
        # Common industry hierarchies (can be expanded)
        self.industry_hierarchies = {
            'information technology': {
                'computer hardware': {
                    'gpus': ['gpu', 'graphics processing unit', 'graphics card', 'gpu chip', 'ai chip'],
                    'cpus': ['cpu', 'processor', 'microprocessor', 'chip'],
                    'memory': ['memory', 'ram', 'storage', 'ssd', 'hdd'],
                    'servers': ['server', 'data center', 'enterprise hardware'],
                },
                'software': {
                    'enterprise software': ['enterprise', 'saas', 'b2b software'],
                    'consumer software': ['consumer', 'b2c', 'mobile app'],
                    'ai software': ['ai software', 'ml platform', 'ai tools'],
                },
                'cloud computing': {
                    'iaas': ['infrastructure as a service', 'cloud infrastructure'],
                    'saas': ['software as a service', 'cloud software'],
                    'paas': ['platform as a service', 'cloud platform'],
                },
            },
            'healthcare': {
                'medical devices': {
                    'diagnostic devices': ['diagnostic', 'imaging', 'scanner'],
                    'therapeutic devices': ['therapeutic', 'treatment', 'surgical'],
                },
                'biotech': {
                    'pharmaceuticals': ['pharma', 'drug', 'medication'],
                    'genomics': ['genomics', 'dna', 'genetic'],
                },
            },
            'financial services': {
                'fintech': {
                    'payments': ['payment', 'transaction', 'processing'],
                    'lending': ['lending', 'loan', 'credit'],
                    'trading': ['trading', 'exchange', 'brokerage'],
                },
            },
        }
    
    def parse_industry_hierarchy(self, industry: str, vertical: str = '', description: str = '') -> Dict[str, str]:
        """
        Parse industry information to extract hierarchical classification
        
        Args:
            industry: Broad industry (e.g., "Information Technology")
            vertical: Specific vertical if available (e.g., "Computer Hardware")
            description: Company description for additional context
            
        Returns:
            Dict with:
            - industry_broad: Broad category (e.g., "Information Technology")
            - industry_specific: Specific sub-industry (e.g., "Computer Hardware")
            - industry_niche: Most specific niche (e.g., "GPUs")
            - industry_full: Full hierarchy string (e.g., "IT → Computer Hardware → GPUs")
        """
        if not industry:
            return {
                'industry_broad': '',
                'industry_specific': '',
                'industry_niche': '',
                'industry_full': '',
            }
        
        industry_lower = industry.lower().strip()
        vertical_lower = vertical.lower().strip() if vertical else ''
        description_lower = description.lower().strip() if description else ''
        
        # Combine all text for analysis
        all_text = f"{industry_lower} {vertical_lower} {description_lower}".lower()
        
        # Try to match against known hierarchies
        hierarchy = self._find_hierarchy_match(industry_lower, vertical_lower, all_text)
        
        if hierarchy:
            return hierarchy
        
        # If no match, try to infer from keywords
        inferred = self._infer_hierarchy(industry_lower, vertical_lower, all_text)
        
        return inferred
    
    def _find_hierarchy_match(self, industry: str, vertical: str, all_text: str) -> Optional[Dict[str, str]]:
        """Find matching hierarchy from known structures"""
        for broad_category, sub_categories in self.industry_hierarchies.items():
            if broad_category in industry or industry in broad_category:
                # Found broad category match
                broad = self._capitalize_industry(broad_category)
                
                # Look for specific sub-category
                specific = ''
                niche = ''
                
                for sub_cat, niches in sub_categories.items():
                    if sub_cat in all_text or any(keyword in all_text for keyword in [sub_cat]):
                        specific = self._capitalize_industry(sub_cat)
                        
                        # Look for niche
                        for niche_name, keywords in niches.items():
                            if any(keyword in all_text for keyword in keywords):
                                niche = self._capitalize_industry(niche_name)
                                break
                        
                        if not niche and vertical:
                            # Use vertical as specific if no niche found
                            specific = self._capitalize_industry(vertical)
                        
                        break
                
                # Build full hierarchy string
                hierarchy_parts = [broad]
                if specific:
                    hierarchy_parts.append(specific)
                if niche:
                    hierarchy_parts.append(niche)
                
                industry_full = ' → '.join(hierarchy_parts)
                
                return {
                    'industry_broad': broad,
                    'industry_specific': specific if specific else '',
                    'industry_niche': niche if niche else '',
                    'industry_full': industry_full,
                }
        
        return None
    
    def _infer_hierarchy(self, industry: str, vertical: str, all_text: str) -> Dict[str, str]:
        """Infer hierarchy from keywords when no exact match"""
        broad = self._capitalize_industry(industry)
        specific = self._capitalize_industry(vertical) if vertical else ''
        niche = ''
        
        # Common patterns to detect
        if 'gpu' in all_text or 'graphics processing' in all_text or 'graphics card' in all_text:
            niche = 'GPUs'
            if not specific:
                specific = 'Computer Hardware'
        elif 'cpu' in all_text or 'processor' in all_text or 'microprocessor' in all_text:
            niche = 'CPUs'
            if not specific:
                specific = 'Computer Hardware'
        elif 'chip' in all_text and ('ai' in all_text or 'machine learning' in all_text):
            niche = 'AI Chips'
            if not specific:
                specific = 'Computer Hardware'
        elif 'hardware' in all_text:
            if not specific:
                specific = 'Computer Hardware'
        
        # Build hierarchy
        hierarchy_parts = [broad]
        if specific:
            hierarchy_parts.append(specific)
        if niche:
            hierarchy_parts.append(niche)
        
        industry_full = ' → '.join(hierarchy_parts) if len(hierarchy_parts) > 1 else broad
        
        return {
            'industry_broad': broad,
            'industry_specific': specific,
            'industry_niche': niche,
            'industry_full': industry_full,
        }
    
    def _capitalize_industry(self, text: str) -> str:
        """Capitalize industry name properly"""
        if not text:
            return ''
        
        # Handle common abbreviations
        abbrevs = {
            'it': 'IT',
            'ai': 'AI',
            'ml': 'ML',
            'gpu': 'GPU',
            'cpu': 'CPU',
            'saas': 'SaaS',
            'paas': 'PaaS',
            'iaas': 'IaaS',
        }
        
        text_lower = text.lower()
        if text_lower in abbrevs:
            return abbrevs[text_lower]
        
        # Capitalize each word
        words = text.split()
        capitalized = []
        for word in words:
            if word.lower() in abbrevs:
                capitalized.append(abbrevs[word.lower()])
            else:
                capitalized.append(word.capitalize())
        
        return ' '.join(capitalized)
    
    def get_specific_search_terms(self, hierarchy: Dict[str, str]) -> List[str]:
        """
        Generate specific search terms based on industry hierarchy
        
        Returns list of search terms ordered from most specific to least specific
        """
        terms = []
        
        if hierarchy.get('industry_niche'):
            terms.append(hierarchy['industry_niche'])
        if hierarchy.get('industry_specific'):
            terms.append(hierarchy['industry_specific'])
        if hierarchy.get('industry_broad'):
            terms.append(hierarchy['industry_broad'])
        
        return terms
