"""
Google Colab Setup Script for VC Firm Filter
Run this cell in Google Colab to set up the environment
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages for Colab"""
    packages = [
        'streamlit>=1.28.0',
        'pandas>=2.0.0', 
        'openpyxl>=3.1.0',
        'openai>=1.0.0',
        'google-generativeai>=0.3.0',
        'numpy>=1.24.0',
        'python-dotenv>=1.0.0'
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("✅ All packages installed successfully!")

def setup_streamlit_tunnel():
    """Setup Streamlit tunnel for Colab"""
    print("🔧 Setting up Streamlit tunnel...")
    print("""
    To run the app in Colab:
    
    1. Upload all Python files to Colab
    2. Set your OpenAI API key:
       import os
       os.environ['OPENAI_API_KEY'] = 'your_key_here'
    
    3. Run the app:
       !streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
    
    4. Click the generated public URL to access the app
    """)

if __name__ == "__main__":
    install_requirements()
    setup_streamlit_tunnel()
