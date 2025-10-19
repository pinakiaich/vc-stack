import pandas as pd
import streamlit as st
from typing import Dict, List, Any
import logging

class ExcelProcessor:
    """Handles Excel file processing and data validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_excel(self, uploaded_file, skip_rows: int = 0) -> pd.DataFrame:
        """
        Process uploaded Excel file and return cleaned DataFrame
        
        Args:
            uploaded_file: Streamlit uploaded file object
            skip_rows: Number of metadata rows to skip (default: auto-detect)
            
        Returns:
            pd.DataFrame: Processed firm data
        """
        try:
            # Try to auto-detect header row if skip_rows not specified
            if skip_rows == 0:
                skip_rows = self._detect_header_row(uploaded_file)
            
            # Reset file pointer
            uploaded_file.seek(0)
            
            # Read Excel file, skipping metadata rows
            if skip_rows > 0:
                df = pd.read_excel(uploaded_file, engine='openpyxl', skiprows=skip_rows)
            else:
                df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            # Clean and validate data
            df = self._clean_data(df)
            df = self._remove_metadata_rows(df)
            df = self._add_missing_columns(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error processing Excel file: {str(e)}")
            raise Exception(f"Failed to process Excel file: {str(e)}")
    
    def _detect_header_row(self, uploaded_file) -> int:
        """Detect which row contains the actual column headers"""
        try:
            # Read first 20 rows without headers to inspect
            df_peek = pd.read_excel(uploaded_file, engine='openpyxl', header=None, nrows=20)
            
            # Look for common company data column names
            company_keywords = ['name', 'company', 'firm', 'organization', 'business']
            metadata_keywords = ['downloaded', 'created', 'search', 'criteria', 'link', 'export']
            
            for idx, row in df_peek.iterrows():
                row_str = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
                
                # Check if this row contains company column headers
                if any(keyword in row_str for keyword in company_keywords):
                    self.logger.info(f"Detected header row at index {idx}")
                    return idx
                
                # Skip metadata rows
                if any(keyword in row_str for keyword in metadata_keywords):
                    continue
            
            return 0  # Default to first row
            
        except Exception as e:
            self.logger.warning(f"Could not detect header row: {e}")
            return 0
    
    def _remove_metadata_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows that look like metadata instead of company data"""
        if len(df) == 0:
            return df
        
        # Check first column for metadata patterns
        first_col = df.columns[0]
        metadata_patterns = [
            'downloaded', 'created', 'search', 'criteria', 'link', 
            'export', 'generated', 'report', 'filter', 'query'
        ]
        
        # Remove rows where first column matches metadata patterns
        mask = df[first_col].str.lower().str.contains('|'.join(metadata_patterns), na=False)
        df = df[~mask]
        
        # Remove rows where name/first column is mostly numeric or IDs
        # (like "466959-97", "59199-40")
        id_pattern = r'^\d+[-_]\d+$'
        mask_ids = df[first_col].str.match(id_pattern, na=False)
        df = df[~mask_ids]
        
        # Remove rows where first column is very short (< 3 chars) or empty
        mask_short = (df[first_col].str.len() < 3) | (df[first_col] == '') | (df[first_col] == 'nan')
        df = df[~mask_short]
        
        return df.reset_index(drop=True)
    
    def clean_empty_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows where the name column is empty or invalid"""
        if 'name' not in df.columns or len(df) == 0:
            return df
        
        # Remove rows with empty, very short, or 'nan' names
        mask_valid = (
            (df['name'] != '') & 
            (df['name'] != 'nan') & 
            (df['name'].str.len() >= 3) &
            (~df['name'].str.match(r'^\d+[-_]\d+$', na=False))  # Remove ID patterns
        )
        
        df_cleaned = df[mask_valid].reset_index(drop=True)
        
        rows_removed = len(df) - len(df_cleaned)
        if rows_removed > 0:
            self.logger.info(f"Removed {rows_removed} rows with invalid/empty names")
        
        return df_cleaned
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize DataFrame"""
        # Remove empty rows
        df = df.dropna(how='all')
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Fill missing values
        df = df.fillna('')
        
        # Convert to string for consistency
        for col in df.columns:
            df[col] = df[col].astype(str)
        
        return df
    
    def _add_missing_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add missing required columns with default values"""
        # Define required columns with alternative names to look for
        column_mappings = {
            'name': ['name', 'company', 'company name', 'firm', 'organization', 'business name', 'company_name'],
            'description': ['description', 'desc', 'about', 'summary', 'overview', 'business description'],
            'stage': ['stage', 'funding stage', 'round', 'series', 'funding round'],
            'revenue': ['revenue', 'arr', 'annual revenue', 'sales', 'mrr'],
            'industry': ['industry', 'sector', 'vertical', 'category', 'market'],
            'location': ['location', 'hq', 'headquarters', 'city', 'region', 'country']
        }
        
        for target_col, alternatives in column_mappings.items():
            if target_col not in df.columns:
                # Look for alternative column names
                found = False
                for alt in alternatives:
                    matching_cols = [col for col in df.columns if alt in col.lower()]
                    if matching_cols:
                        df[target_col] = df[matching_cols[0]]
                        self.logger.info(f"Mapped '{matching_cols[0]}' to '{target_col}'")
                        found = True
                        break
                
                if not found:
                    # Try fuzzy matching as fallback
                    similar_col = self._find_similar_column(df.columns, target_col)
                    if similar_col:
                        df[target_col] = df[similar_col]
                        self.logger.info(f"Fuzzy matched '{similar_col}' to '{target_col}'")
                    else:
                        # Last resort: use first non-empty column for 'name'
                        if target_col == 'name' and len(df.columns) > 0:
                            df[target_col] = df[df.columns[0]]
                            self.logger.warning(f"Using first column '{df.columns[0]}' as 'name'")
                        else:
                            df[target_col] = ''
                            self.logger.warning(f"No match found for '{target_col}', using empty string")
        
        return df
    
    def _find_similar_column(self, columns: List[str], target: str) -> str:
        """Find similar column name for mapping"""
        target_lower = target.lower()
        
        for col in columns:
            col_lower = col.lower()
            if (target_lower in col_lower or 
                col_lower in target_lower or
                self._calculate_similarity(target_lower, col_lower) > 0.7):
                return col
        
        return None
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate simple string similarity"""
        if not str1 or not str2:
            return 0.0
        
        common_chars = sum(1 for c in str1 if c in str2)
        return common_chars / max(len(str1), len(str2))
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate processed data and return statistics"""
        stats = {
            'total_firms': len(df),
            'columns': list(df.columns),
            'missing_data': df.isnull().sum().to_dict(),
            'sample_firms': df.head(3).to_dict('records')
        }
        
        return stats
