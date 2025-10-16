import os
import streamlit as st
from typing import Optional, Dict
import logging

class Config:
    """Configuration management for the VC Filter app"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_environment()
    
    def _setup_environment(self):
        """Setup environment variables and configuration"""
        # Set default logging level
        logging.basicConfig(level=logging.INFO)
        
        # Configure Streamlit secrets
        if hasattr(st, 'secrets'):
            self._load_streamlit_secrets()
    
    def _load_streamlit_secrets(self):
        """Load configuration from Streamlit secrets"""
        try:
            # This will work in Streamlit Cloud/Colab with secrets
            if hasattr(st.secrets, 'get'):
                self.openai_key = st.secrets.get("OPENAI_API_KEY")
                self.gemini_key = st.secrets.get("GEMINI_API_KEY")
            else:
                self.openai_key = None
                self.gemini_key = None
        except Exception as e:
            self.logger.warning(f"Could not load Streamlit secrets: {e}")
            self.openai_key = None
            self.gemini_key = None
    
    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key from environment or secrets"""
        # Priority order: env var > streamlit secrets > user input
        key = os.getenv('OPENAI_API_KEY')
        
        if not key and hasattr(self, 'openai_key') and self.openai_key:
            key = self.openai_key
        
        if not key:
            # Fallback to session state for user input
            key = st.session_state.get('openai_key')
        
        return key
    
    def get_gemini_key(self) -> Optional[str]:
        """Get Gemini API key from environment or secrets"""
        key = os.getenv('GEMINI_API_KEY')
        
        if not key and hasattr(self, 'gemini_key') and self.gemini_key:
            key = self.gemini_key
        
        if not key:
            key = st.session_state.get('gemini_key')
        
        return key
    
    def setup_api_keys_ui(self) -> bool:
        """Setup UI for API key input if not available"""
        openai_key = self.get_openai_key()
        
        if not openai_key:
            with st.sidebar:
                st.markdown("### 🔑 API Configuration")
                st.markdown("Enter your OpenAI API key to use AI filtering:")
                
                openai_key = st.text_input(
                    "OpenAI API Key",
                    type="password",
                    help="Get your key from https://platform.openai.com/api-keys"
                )
                
                if openai_key:
                    st.session_state['openai_key'] = openai_key
                    st.success("✅ API key saved!")
                    return True
                else:
                    st.warning("⚠️ API key required for AI filtering")
                    return False
        
        return True
    
    def get_database_url(self) -> str:
        """Get database URL for backend connection"""
        return os.getenv('DATABASE_URL', 'sqlite:///./local.db')
    
    def get_log_level(self) -> str:
        """Get logging level"""
        return os.getenv('LOG_LEVEL', 'INFO')
    
    def is_colab_environment(self) -> bool:
        """Check if running in Google Colab"""
        try:
            import google.colab
            return True
        except ImportError:
            return False
    
    def get_max_firms_to_analyze(self) -> int:
        """Get maximum number of firms to analyze in one batch"""
        return int(os.getenv('MAX_FIRMS_BATCH', '50'))
    
    def get_ai_model(self) -> str:
        """Get AI model to use"""
        return os.getenv('AI_MODEL', 'gpt-3.5-turbo')
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate current configuration"""
        return {
            'openai_available': bool(self.get_openai_key()),
            'gemini_available': bool(self.get_gemini_key()),
            'database_configured': bool(self.get_database_url()),
            'colab_environment': self.is_colab_environment()
        }
