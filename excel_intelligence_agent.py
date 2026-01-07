"""
Excel Intelligence Agent
Intelligently scans Excel sheet to extract company information like a VC analyst would.
Understands various column naming conventions, extracts opportunity/exit scores, and finds stage data
in columns like "First Financing Deal Type 2".
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
            - opportunity_score: Opportunity score/metric
            - exit_probability_score: Exit probability score/metric
        """
        self.logger.info(f"Extracting data for company: {company_name}")
        
        # Step 1: Find the company row using intelligent matching
        company_row = self._find_company_row(company_name, df)
        
        if company_row is None:
            self.logger.warning(f"Company '{company_name}' not found in Excel sheet")
            return self._get_empty_data()
        
        # Step 2: Intelligently extract all available fields (VC analyst approach)
        extracted_data = {
            'industry': self._extract_industry(company_row, df),
            'sector': self._extract_industry(company_row, df),  # Same as industry
            'vertical': self._extract_vertical(company_row, df),
            'stage': self._extract_stage(company_row, df),
            'description': self._extract_description(company_row, df),
            'location': self._extract_location(company_row, df),
            'revenue': self._extract_revenue(company_row, df),
            'opportunity_score': self._extract_opportunity_score(company_row, df),
            'exit_probability_score': self._extract_exit_probability_score(company_row, df),
        }
        
        # Log what was found
        found_fields = [k for k, v in extracted_data.items() if v and v != '']
        missing_fields = [k for k, v in extracted_data.items() if not v or v == '']
        
        self.logger.info(f"Extracted {len(found_fields)} fields for {company_name}: {', '.join(found_fields)}")
        if missing_fields:
            self.logger.warning(f"Missing fields for {company_name}: {', '.join(missing_fields)}")
            # Log available columns to help debug
            self.logger.info(f"Available columns in Excel: {list(df.columns)}")
            # Special logging for stage
            if 'stage' in missing_fields:
                self.logger.warning(f"⚠️ STAGE NOT FOUND for {company_name}")
                self.logger.warning(f"Looking for: 'First Financing Deal Type 2'")
                # Check if the column exists
                for col in df.columns:
                    col_lower = col.lower()
                    if 'first' in col_lower and 'financing' in col_lower and 'deal' in col_lower and 'type' in col_lower:
                        self.logger.warning(f"Found potential match: '{col}' - checking value...")
                        stage_value = company_row.get(col, '')
                        self.logger.warning(f"Value in '{col}': '{stage_value}'")
        
        return extracted_data
    
    def _find_company_row(self, company_name: str, df: pd.DataFrame) -> Optional[pd.Series]:
        """Find company row using intelligent matching - VC analyst approach"""
        # VC analyst approach: be flexible with column names
        name_column = None
        name_columns_to_try = ['name', 'company', 'companies', 'company name', 'firm', 'organization', 'business name']
        
        # Find the name column
        for col_name in name_columns_to_try:
            if col_name in df.columns:
                name_column = col_name
                break
        
        # If still not found, look for any column containing 'name' or 'company'
        if not name_column:
            for col in df.columns:
                col_lower = col.lower()
                if 'name' in col_lower or 'company' in col_lower:
                    name_column = col
                    break
        
        if not name_column:
            self.logger.error(f"Name column not found. Available columns: {list(df.columns)}")
            return None
        
        company_name_clean = company_name.strip().lower()
        
        # Strategy 1: Exact match (case-insensitive)
        exact_match = df[df[name_column].str.strip().str.lower() == company_name_clean]
        if not exact_match.empty:
            self.logger.info(f"Found exact match for '{company_name}' in column '{name_column}'")
            return exact_match.iloc[0]
        
        # Strategy 2: Partial match (company name contains search term or vice versa)
        for idx, row in df.iterrows():
            row_name = str(row.get(name_column, '')).strip().lower()
            if company_name_clean in row_name or row_name in company_name_clean:
                if len(row_name) > 3 and len(company_name_clean) > 3:  # Avoid false matches
                    self.logger.info(f"Found partial match for '{company_name}': '{row[name_column]}'")
                    return row
        
        # Strategy 3: Fuzzy match (remove common words and match) - VC analyst approach
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
                row_name = str(row.get(name_column, '')).strip().lower()
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
                    self.logger.info(f"Found fuzzy match for '{company_name}': '{row[name_column]}' (common words: {common_words})")
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
        """Extract funding stage from row - VC analyst approach"""
        # CRITICAL: User specified "First Financing Deal Type 2" - check this FIRST with exact and flexible matching
        # Try exact match first (case-insensitive, handle spaces)
        target_column = None
        
        # Strategy 1: Exact match (case-insensitive, normalize spaces)
        for col in df.columns:
            col_normalized = ' '.join(col.lower().split())  # Normalize spaces
            target_normalized = ' '.join('first financing deal type 2'.lower().split())
            if col_normalized == target_normalized:
                target_column = col
                self.logger.info(f"Found exact match for 'First Financing Deal Type 2': '{col}'")
                break
        
        # Strategy 2: Contains match (if exact didn't work)
        if not target_column:
            for col in df.columns:
                col_lower = col.lower().strip()
                # Check if column contains all key words
                if 'first' in col_lower and 'financing' in col_lower and 'deal' in col_lower and 'type' in col_lower and '2' in col_lower:
                    target_column = col
                    self.logger.info(f"Found flexible match for 'First Financing Deal Type 2': '{col}'")
                    break
        
        # Strategy 3: Try the exact column name as-is (in case it's exactly "First Financing Deal Type 2")
        if not target_column and 'First Financing Deal Type 2' in df.columns:
            target_column = 'First Financing Deal Type 2'
            self.logger.info(f"Found exact column name 'First Financing Deal Type 2'")
        
        # If we found the target column, use it
        if target_column:
            value = row.get(target_column, '')
            if pd.notna(value):
                value_str = str(value).strip()
                if value_str and value_str.lower() not in ['nan', 'none', 'n/a', '', 'null', 'undefined']:
                    stage = self._normalize_stage(value_str)
                    if stage:
                        self.logger.info(f"✅ Extracted stage '{stage}' from '{target_column}'")
                        return stage
                    else:
                        self.logger.warning(f"Found value '{value_str}' in '{target_column}' but normalization failed")
        
        # Fallback: Try other stage columns (if First Financing Deal Type 2 didn't work)
        stage_columns = [
            'first financing deal type',
            'financing deal type',
            'deal type',
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
            if any(keyword in col_lower for keyword in ['stage', 'round', 'series', 'funding', 'financing', 'capital', 'deal type']):
                if col not in stage_columns:
                    stage_columns.append(col)
        
        # Try each column in priority order
        for col_name in stage_columns:
            if col_name in df.columns:
                value = row.get(col_name, '')
                if pd.notna(value):
                    value_str = str(value).strip()
                    if value_str and value_str.lower() not in ['nan', 'none', 'n/a', '', 'null', 'undefined']:
                        stage = self._normalize_stage(value_str)
                        if stage:
                            self.logger.info(f"Found stage '{stage}' in column '{col_name}'")
                            return stage
        
        # If no stage found, log available columns for debugging
        self.logger.warning(f"❌ Stage not found. Available columns: {list(df.columns)}")
        self.logger.warning(f"Looking for columns containing: 'first financing deal type 2'")
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
    
    def _extract_opportunity_score(self, row: pd.Series, df: pd.DataFrame) -> str:
        """Extract opportunity score - VC analyst approach"""
        # Look for opportunity score columns
        opportunity_columns = [
            'opportunity score',
            'opportunity',
            'opportunity probability',
            'opportunity_score',
            'opp score',
        ]
        
        # Also check for columns containing opportunity keywords
        for col in df.columns:
            col_lower = col.lower().strip()
            if any(keyword in col_lower for keyword in ['opportunity', 'opp score', 'opp_score']):
                if col not in opportunity_columns:
                    opportunity_columns.append(col)
        
        # Try each column
        for col_name in opportunity_columns:
            if col_name in df.columns:
                value = row.get(col_name, '')
                if pd.notna(value):
                    value_str = str(value).strip()
                    if value_str and value_str.lower() not in ['nan', 'none', 'n/a', '', 'null', 'undefined']:
                        self.logger.info(f"Found opportunity score '{value_str}' in column '{col_name}'")
                        return value_str
        
        return ''
    
    def _extract_exit_probability_score(self, row: pd.Series, df: pd.DataFrame) -> str:
        """Extract exit probability score - VC analyst approach"""
        # Look for exit probability score columns
        exit_columns = [
            'exit probability score',
            'exit probability',
            'exit prob',
            'exit_probability_score',
            'exit prob score',
            'exit score',
        ]
        
        # Also check for columns containing exit keywords
        for col in df.columns:
            col_lower = col.lower().strip()
            if any(keyword in col_lower for keyword in ['exit', 'exit prob', 'exit_prob']):
                if col not in exit_columns:
                    exit_columns.append(col)
        
        # Try each column
        for col_name in exit_columns:
            if col_name in df.columns:
                value = row.get(col_name, '')
                if pd.notna(value):
                    value_str = str(value).strip()
                    if value_str and value_str.lower() not in ['nan', 'none', 'n/a', '', 'null', 'undefined']:
                        self.logger.info(f"Found exit probability score '{value_str}' in column '{col_name}'")
                        return value_str
        
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
            'opportunity_score': '',
            'exit_probability_score': '',
        }
