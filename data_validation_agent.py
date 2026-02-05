"""
Data Validation Agent
Validates and cross-checks data at every stage of the workflow
"""
import logging
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class DataValidationAgent:
    """Agent that validates and cross-checks data throughout the workflow"""
    
    def __init__(self):
        self.logger = logger
    
    def validate_excel_data(self, excel_data: Dict, company_name: str) -> Dict:
        """
        Validate data extracted from Excel
        
        Args:
            excel_data: Data extracted from Excel
            company_name: Company name for context
            
        Returns:
            Dict with validation results:
            - is_valid: bool
            - issues: List of issues found
            - missing_fields: List of missing fields
            - recommendations: List of recommendations
        """
        issues = []
        missing_fields = []
        recommendations = []
        
        # Check for required fields
        required_fields = ['name', 'industry']
        for field in required_fields:
            if not excel_data.get(field) or excel_data.get(field) == '':
                missing_fields.append(field)
        
        # Validate revenue format
        revenue = excel_data.get('revenue', '')
        if revenue:
            if not self._is_valid_revenue_format(revenue):
                issues.append(f"Revenue format may be invalid: '{revenue}'")
        
        # Validate stage format
        stage = excel_data.get('stage', '')
        if stage:
            if not self._is_valid_stage_format(stage):
                issues.append(f"Stage format may be invalid: '{stage}'")
        
        # Check for logical inconsistencies
        inconsistencies = self._check_logical_consistency(excel_data)
        issues.extend(inconsistencies)
        
        # Generate recommendations
        if missing_fields:
            recommendations.append(f"Missing fields: {', '.join(missing_fields)}. Consider adding these to Excel.")
        if issues:
            recommendations.append("Some data may need verification. Cross-check with external sources.")
        
        return {
            'is_valid': len(issues) == 0 and len(missing_fields) == 0,
            'issues': issues,
            'missing_fields': missing_fields,
            'recommendations': recommendations,
            'confidence': self._calculate_confidence(excel_data, issues, missing_fields),
        }
    
    def cross_check_data(
        self, 
        excel_data: Dict, 
        research_data: Dict,
        company_name: str
    ) -> Dict:
        """
        Cross-check Excel data against research findings
        
        Args:
            excel_data: Data from Excel
            research_data: Data from research
            company_name: Company name for context
            
        Returns:
            Dict with cross-check results:
            - matches: Fields that match
            - discrepancies: Fields with discrepancies
            - missing_in_excel: Data in research but not Excel
            - missing_in_research: Data in Excel but not research
            - recommendations: Recommendations for resolution
        """
        matches = []
        discrepancies = []
        missing_in_excel = []
        missing_in_research = []
        
        # Compare industry
        excel_industry = excel_data.get('industry', '').lower().strip()
        research_industry = research_data.get('industry', '').lower().strip()
        if excel_industry and research_industry:
            if excel_industry == research_industry or excel_industry in research_industry or research_industry in excel_industry:
                matches.append('industry')
            else:
                discrepancies.append({
                    'field': 'industry',
                    'excel': excel_data.get('industry', ''),
                    'research': research_data.get('industry', ''),
                    'recommendation': 'Verify industry classification'
                })
        
        # Compare stage
        excel_stage = excel_data.get('stage', '').lower().strip()
        research_stage = self._extract_stage_from_research(research_data)
        if excel_stage and research_stage:
            if excel_stage == research_stage or excel_stage in research_stage:
                matches.append('stage')
            else:
                discrepancies.append({
                    'field': 'stage',
                    'excel': excel_data.get('stage', ''),
                    'research': research_stage,
                    'recommendation': 'Verify funding stage'
                })
        
        # Check for data in research but not Excel
        if research_data.get('country_of_incorporation') and not excel_data.get('location'):
            missing_in_excel.append('location/country')
        if research_data.get('founder_profile') and not excel_data.get('founder_info'):
            missing_in_excel.append('founder_info')
        
        # Check for data in Excel but not research
        if excel_data.get('revenue') and not research_data.get('quantitative_data', {}).get('company_revenue'):
            missing_in_research.append('revenue')
        if excel_data.get('stage') and not research_stage:
            missing_in_research.append('stage')
        
        # Generate recommendations
        recommendations = []
        if discrepancies:
            recommendations.append(f"Found {len(discrepancies)} discrepancies. Review and verify:")
            for disc in discrepancies:
                recommendations.append(f"  - {disc['field']}: Excel='{disc['excel']}', Research='{disc['research']}'")
        if missing_in_excel:
            recommendations.append(f"Consider adding to Excel: {', '.join(missing_in_excel)}")
        if missing_in_research:
            recommendations.append(f"Research missing: {', '.join(missing_in_research)}. May need more targeted searches.")
        
        return {
            'matches': matches,
            'discrepancies': discrepancies,
            'missing_in_excel': missing_in_excel,
            'missing_in_research': missing_in_research,
            'recommendations': recommendations,
            'confidence': self._calculate_cross_check_confidence(matches, discrepancies),
        }
    
    def fill_missing_data(
        self, 
        company_data: Dict,
        research_data: Dict,
        excel_data: Dict
    ) -> Dict:
        """
        Fill missing data points from available sources
        
        Args:
            company_data: Current company data
            research_data: Research findings
            excel_data: Excel data
            
        Returns:
            Dict with filled data and source information
        """
        filled_data = company_data.copy()
        data_sources = {}
        
        # Fill from research if missing in company_data
        if not filled_data.get('country_of_incorporation') and research_data.get('country_of_incorporation'):
            filled_data['country_of_incorporation'] = research_data['country_of_incorporation']
            data_sources['country_of_incorporation'] = 'research'
        
        if not filled_data.get('founder_profile') and research_data.get('founder_profile'):
            filled_data['founder_profile'] = research_data['founder_profile']
            data_sources['founder_profile'] = 'research'
        
        # Fill from Excel if missing in company_data
        if not filled_data.get('revenue') and excel_data.get('revenue'):
            filled_data['revenue'] = excel_data['revenue']
            data_sources['revenue'] = 'excel'
        
        if not filled_data.get('stage') and excel_data.get('stage'):
            filled_data['stage'] = excel_data['stage']
            data_sources['stage'] = 'excel'
        
        # Fill quantitative data from research
        quantitative_data = research_data.get('quantitative_data', {})
        if quantitative_data:
            for key, value in quantitative_data.items():
                if value and value != "Not available":
                    filled_data[f'quantitative_{key}'] = value
                    data_sources[f'quantitative_{key}'] = 'research'
        
        return {
            'filled_data': filled_data,
            'data_sources': data_sources,
            'fields_filled': list(data_sources.keys()),
        }
    
    def _is_valid_revenue_format(self, revenue: str) -> bool:
        """Check if revenue string is in valid format"""
        if not revenue:
            return False
        
        # Check for common revenue formats: $10M, $10 million, 10M, etc.
        revenue_patterns = [
            r'\$?\d+(?:\.\d+)?\s*(?:M|million|billion|B|K|thousand)',
            r'\d+(?:\.\d+)?\s*(?:M|million|billion|B|K|thousand)',
        ]
        
        for pattern in revenue_patterns:
            if re.search(pattern, revenue, re.IGNORECASE):
                return True
        
        return False
    
    def _is_valid_stage_format(self, stage: str) -> bool:
        """Check if stage string is in valid format"""
        if not stage:
            return False
        
        valid_stages = [
            'seed', 'pre-seed', 'series a', 'series b', 'series c',
            'series d', 'series e', 'growth', 'late stage', 'ipo'
        ]
        
        stage_lower = stage.lower()
        return any(valid in stage_lower for valid in valid_stages)
    
    def _check_logical_consistency(self, data: Dict) -> List[str]:
        """Check for logical inconsistencies in data"""
        issues = []
        
        # Check if stage and revenue make sense together
        stage = data.get('stage', '').lower()
        revenue = data.get('revenue', '')
        
        if stage and revenue:
            # Extract revenue number
            revenue_match = re.search(r'(\d+(?:\.\d+)?)', revenue)
            if revenue_match:
                revenue_num = float(revenue_match.group(1))
                
                # Check if 'M' or 'B' suffix
                if 'M' in revenue.upper() or 'million' in revenue.lower():
                    revenue_num = revenue_num  # Already in millions
                elif 'B' in revenue.upper() or 'billion' in revenue.lower():
                    revenue_num = revenue_num * 1000  # Convert to millions
                
                # Basic consistency checks
                if 'seed' in stage and revenue_num > 5:
                    issues.append(f"Seed stage company with ${revenue_num}M revenue seems unusual")
                if 'series a' in stage and revenue_num > 50:
                    issues.append(f"Series A company with ${revenue_num}M revenue seems high")
        
        return issues
    
    def _extract_stage_from_research(self, research_data: Dict) -> str:
        """Extract funding stage from research data"""
        # Check company background for stage mentions
        company_bg = research_data.get('company_background', '')
        if company_bg:
            stage_patterns = [
                r'series\s+[a-f]',
                r'seed\s+round',
                r'growth\s+stage',
                r'late\s+stage',
            ]
            for pattern in stage_patterns:
                match = re.search(pattern, company_bg, re.IGNORECASE)
                if match:
                    return match.group(0)
        
        return ''
    
    def _calculate_confidence(self, data: Dict, issues: List, missing_fields: List) -> float:
        """Calculate confidence score for data validity"""
        total_fields = len(['name', 'industry', 'stage', 'revenue', 'description'])
        filled_fields = sum(1 for field in ['name', 'industry', 'stage', 'revenue', 'description'] 
                           if data.get(field) and data.get(field) != '')
        
        completeness = filled_fields / total_fields if total_fields > 0 else 0
        issue_penalty = len(issues) * 0.1
        missing_penalty = len(missing_fields) * 0.15
        
        confidence = max(0, min(1, completeness - issue_penalty - missing_penalty))
        return confidence
    
    def _calculate_cross_check_confidence(self, matches: List, discrepancies: List) -> float:
        """Calculate confidence based on cross-check results"""
        total_checks = len(matches) + len(discrepancies)
        if total_checks == 0:
            return 0.5  # Neutral if no checks performed
        
        match_ratio = len(matches) / total_checks
        return match_ratio
