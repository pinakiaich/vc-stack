"""
Excel Intelligence Agent
Intelligently scans Excel sheet to extract company information including industry, vertical, and funding stage
"""
import pandas as pd
import logging
from typing import Dict, Optional, List
import re

logger = logging.getLogger(__name__)


class ExcelIntelligenceAgent:
    """Agent that intelligently extracts company data from Excel sheets"""
    
    def __init__(self):
        self.logger = logger
    
    def extract_company_data(self, company_name: str, df: pd.DataFrame) -> Dict:
        """
        Intelligently extract company data from Excel DataFrame
        
        Args:
            company_name: Name of the company to find
            df: DataFrame containing Excel data
            
        Returns:
            Dict with extracted company information:
            - industry: Primary industry/vertical
            - sector: Industry sector (same as industry)
            - stage: Funding stage (e.g., Series A, Series B, Seed)
            - description: Company description
            - location: Company location
            - revenue: Revenue information
            - vertical: Specific vertical/sub-industry
        """
        self.logger.info(f"Extracting data for company: {company_name}")
        
        # Step 1: Find the company row using intelligent matching
        company_row = self._find_company_row(company_name, df)
        
        if company_row is None:
            self.logger.warning(f"Company '{company_name}' not found in Excel sheet")
            return self._get_empty_data()
        
        # Step 2: Intelligently extract all available fields
        extracted_data = {
            'industry': self._extract_industry(company_row, df),
            'sector': self._extract_industry(company_row, df),  # Same as industry
            'vertical': self._extract_vertical(company_row, df),
            'stage': self._extract_stage(company_row, df),
            'description': self._extract_description(company_row, df),
            'location': self._extract_location(company_row, df),
            'revenue': self._extract_revenue(company_row, df),
        }
        
        # Log what was found
        found_fields = [k for k, v in extracted_data.items() if v and v != '']
        missing_fields = [k for k, v in extracted_data.items() if not v or v == '']
        
        self.logger.info(f"Extracted {len(found_fields)} fields for {company_name}: {', '.join(found_fields)}")
        if missing_fields:
            self.logger.warning(f"Missing fields for {company_name}: {', '.join(missing_fields)}")
            # Log available columns to help debug
            self.logger.info(f"Available columns in Excel: {list(df.columns)}")
        
        return extracted_data
    
    def _find_company_row(self, company_name: str, df: pd.DataFrame) -> Optional[pd.Series]:
        """Find company row using intelligent matching"""
        if 'name' not in df.columns:
            self.logger.error("'name' column not found in DataFrame")
            return None
        
        company_name_clean = company_name.strip().lower()
        
        # Strategy 1: Exact match (case-insensitive)
        exact_match = df[df['name'].str.strip().str.lower() == company_name_clean]
        if not exact_match.empty:
            self.logger.info(f"Found exact match for '{company_name}'")
            return exact_match.iloc[0]
        
        # Strategy 2: Partial match (company name contains search term or vice versa)
        for idx, row in df.iterrows():
            row_name = str(row.get('name', '')).strip().lower()
            if company_name_clean in row_name or row_name in company_name_clean:
                if len(row_name) > 3 and len(company_name_clean) > 3:  # Avoid false matches
                    self.logger.info(f"Found partial match for '{company_name}': '{row['name']}'")
                    return row
        
        # Strategy 3: Fuzzy match (remove common words and match)
        company_name_words = set(re.findall(r'\w+', company_name_clean))
        company_name_words.discard('inc')
        company_name_words.discard('llc')
        company_name_words.discard('ltd')
        company_name_words.discard('corp')
        company_name_words.discard('company')
        company_name_words.discard('technologies')
        company_name_words.discard('tech')
        
        if len(company_name_words) >= 2:  # Need at least 2 meaningful words
            for idx, row in df.iterrows():
                row_name = str(row.get('name', '')).strip().lower()
                row_words = set(re.findall(r'\w+', row_name))
                row_words.discard('inc')
                row_words.discard('llc')
                row_words.discard('ltd')
                row_words.discard('corp')
                row_words.discard('company')
                row_words.discard('technologies')
                row_words.discard('tech')
                
                # Check if significant words overlap
                common_words = company_name_words.intersection(row_words)
                if len(common_words) >= 2:
                    self.logger.info(f"Found fuzzy match for '{company_name}': '{row['name']}' (common words: {common_words})")
                    return row
        
        return None
    
    def _extract_industry(self, row: pd.Series, df: pd.DataFrame) -> str:
        """Extract industry from row, checking multiple possible column names"""
        # Priority order for industry columns
        industry_columns = [
            'industry',
            'sector',
            'primary industry',
            'primary industry sector',
            'industry sector',
            'vertical',
            'category',
            'market',
            'business sector',
            'industry category',
        ]
        
        # Also check for columns containing these keywords
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['industry', 'sector', 'vertical', 'category']):
                if col not in industry_columns:
                    industry_columns.append(col)
        
        # Try each column in priority order
        for col_name in industry_columns:
            if col_name in df.columns:
                value = row.get(col_name, '')
                if pd.notna(value) and str(value).strip() and str(value).strip().lower() not in ['nan', 'none', 'n/a', '']:
                    return str(value).strip()
        
        return ''
    
    def _extract_vertical(self, row: pd.Series, df: pd.DataFrame) -> str:
        """Extract specific vertical/sub-industry"""
        # Check for vertical-specific columns
        vertical_columns = [
            'vertical',
            'sub industry',
            'sub-industry',
            'niche',
            'segment',
            'market segment',
            'industry vertical',
        ]
        
        for col_name in vertical_columns:
            if col_name in df.columns:
                value = row.get(col_name, '')
                if pd.notna(value) and str(value).strip() and str(value).strip().lower() not in ['nan', 'none', 'n/a', '']:
                    return str(value).strip()
        
        # If no vertical column, try to extract from industry description
        industry = self._extract_industry(row, df)
        if industry:
            # Try to identify sub-vertical from industry name
            # E.g., "Artificial Intelligence - Healthcare" -> "Healthcare"
            if ' - ' in industry:
                parts = industry.split(' - ')
                if len(parts) > 1:
                    return parts[-1].strip()
            elif '|' in industry:
                parts = industry.split('|')
                if len(parts) > 1:
                    return parts[-1].strip()
        
        return ''
    
    def _extract_stage(self, row: pd.Series, df: pd.DataFrame) -> str:
        """Extract funding stage from row"""
        # Priority order for stage columns
        stage_columns = [
            'stage',
            'funding stage',
            'round',
            'series',
            'funding round',
            'investment stage',
            'capital stage',
            'financing stage',
        ]
        
        # Also check for columns containing these keywords (case-insensitive)
        for col in df.columns:
            col_lower = col.lower().strip()
            # Check if column name contains stage-related keywords
            if any(keyword in col_lower for keyword in ['stage', 'round', 'series', 'funding', 'financing', 'capital']):
                if col not in stage_columns:
                    stage_columns.append(col)
        
        # Try each column in priority order
        for col_name in stage_columns:
            if col_name in df.columns:
                value = row.get(col_name, '')
                # More robust checking
                if pd.notna(value):
                    value_str = str(value).strip()
                    # Check if it's a valid stage value
                    if value_str and value_str.lower() not in ['nan', 'none', 'n/a', '', 'null', 'undefined']:
                        stage = value_str
                        # Normalize stage names
                        stage = self._normalize_stage(stage)
                        if stage:  # Only return if normalization produced a valid result
                            self.logger.info(f"Found stage '{stage}' in column '{col_name}'")
                            return stage
        
        # If no stage found, log available columns for debugging
        self.logger.warning(f"Stage not found. Available columns: {list(df.columns)}")
        return ''
    
    def _normalize_stage(self, stage: str) -> str:
        """Normalize funding stage names to standard format"""
        if not stage or not stage.strip():
            return ''
        
        stage_lower = stage.lower().strip()
        
        # Map common variations to standard names
        stage_mapping = {
            'seed': 'Seed',
            'pre-seed': 'Pre-Seed',
            'pre seed': 'Pre-Seed',
            'preseed': 'Pre-Seed',
            'series a': 'Series A',
            'series b': 'Series B',
            'series c': 'Series C',
            'series d': 'Series D',
            'series e': 'Series E',
            'series f': 'Series F',
            'seriesa': 'Series A',
            'seriesb': 'Series B',
            'seriesc': 'Series C',
            'growth': 'Growth',
            'late stage': 'Late Stage',
            'late-stage': 'Late Stage',
            'latestage': 'Late Stage',
            'ipo': 'IPO',
            'acquired': 'Acquired',
            'angel': 'Angel',
            'angel round': 'Angel',
        }
        
        # Check for exact matches first
        for key, standard in stage_mapping.items():
            if key == stage_lower:
                return standard
        
        # Check for partial matches (contains)
        for key, standard in stage_mapping.items():
            if key in stage_lower:
                return standard
        
        # Check for patterns like "Series A", "Series B" etc.
        import re
        series_match = re.search(r'series\s*([a-f])', stage_lower)
        if series_match:
            letter = series_match.group(1).upper()
            return f'Series {letter}'
        
        # If no match, capitalize first letter of each word (preserve original if it looks valid)
        words = stage.split()
        if len(words) > 0:
            normalized = ' '.join(word.capitalize() for word in words)
            # Return original if it's already in a reasonable format
            if len(normalized) > 1 and normalized[0].isupper():
                return normalized
        
        return stage.strip()  # Return original if we can't normalize
    
    def _extract_description(self, row: pd.Series, df: pd.DataFrame) -> str:
        """Extract company description"""
        desc_columns = [
            'description',
            'desc',
            'about',
            'summary',
            'overview',
            'business description',
            'company description',
        ]
        
        for col_name in desc_columns:
            if col_name in df.columns:
                value = row.get(col_name, '')
                if pd.notna(value) and str(value).strip() and str(value).strip().lower() not in ['nan', 'none', 'n/a', '']:
                    return str(value).strip()
        
        return ''
    
    def _extract_location(self, row: pd.Series, df: pd.DataFrame) -> str:
        """Extract company location"""
        location_columns = [
            'location',
            'hq',
            'headquarters',
            'city',
            'region',
            'country',
            'geography',
        ]
        
        for col_name in location_columns:
            if col_name in df.columns:
                value = row.get(col_name, '')
                if pd.notna(value) and str(value).strip() and str(value).strip().lower() not in ['nan', 'none', 'n/a', '']:
                    return str(value).strip()
        
        return ''
    
    def _extract_revenue(self, row: pd.Series, df: pd.DataFrame) -> str:
        """Extract revenue information"""
        revenue_columns = [
            'revenue',
            'arr',
            'annual revenue',
            'sales',
            'mrr',
            'total revenue',
        ]
        
        for col_name in revenue_columns:
            if col_name in df.columns:
                value = row.get(col_name, '')
                if pd.notna(value) and str(value).strip() and str(value).strip().lower() not in ['nan', 'none', 'n/a', '']:
                    return str(value).strip()
        
        return ''
    
    def _get_empty_data(self) -> Dict:
        """Return empty data structure"""
        return {
            'industry': '',
            'sector': '',
            'vertical': '',
            'stage': '',
            'description': '',
            'location': '',
            'revenue': '',
        }
