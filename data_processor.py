import pandas as pd
import streamlit as st
from typing import Dict, List, Any
import logging

class ExcelProcessor:
    """Handles Excel file processing and data validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_excel(self, uploaded_file) -> pd.DataFrame:
        """
        Process uploaded Excel file and return cleaned DataFrame
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            pd.DataFrame: Processed firm data
        """
        try:
            # Read Excel file
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            
            # Clean and validate data
            df = self._clean_data(df)
            df = self._add_missing_columns(df)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error processing Excel file: {str(e)}")
            raise Exception(f"Failed to process Excel file: {str(e)}")
    
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
        required_columns = {
            'name': 'name',
            'description': 'description', 
            'stage': 'stage',
            'revenue': 'revenue',
            'industry': 'industry',
            'location': 'location'
        }
        
        for col, default in required_columns.items():
            if col not in df.columns:
                # Try to find similar column names
                similar_col = self._find_similar_column(df.columns, col)
                if similar_col:
                    df[col] = df[similar_col]
                else:
                    df[col] = default
        
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
