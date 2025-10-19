import streamlit as st
import pandas as pd
from data_processor import ExcelProcessor
from ai_filter import AIFilter
from config import Config

st.set_page_config(
    page_title="VC Firm Filter",
    page_icon="🎯",
    layout="wide"
)

def main():
    st.title("🎯 VC Firm Filter")
    st.markdown("Upload Excel sheet with firms and enter heuristics to filter top 10 matches")
    
    # Initialize components
    config = Config()
    processor = ExcelProcessor()
    
    # API Key Configuration Section (at top, prominent)
    openai_key = config.get_openai_key()
    
    if not openai_key:
        st.warning("⚠️ **OpenAI API Key Required** - Please enter your API key below to enable AI-powered filtering")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            api_key_input = st.text_input(
                "🔑 Enter your OpenAI API Key",
                type="password",
                placeholder="sk-...",
                help="Get your API key from https://platform.openai.com/api-keys",
                key="api_key_input"
            )
        with col2:
            if st.button("Save API Key", type="primary"):
                if api_key_input and api_key_input.startswith('sk-'):
                    st.session_state['openai_key'] = api_key_input
                    st.success("✅ API Key saved!")
                    st.rerun()
                elif api_key_input:
                    st.error("❌ Invalid API key format")
                else:
                    st.error("❌ Please enter an API key")
        
        st.info("💡 **Tip:** Once you enter your API key, you'll be able to use AI-powered filtering")
        st.divider()
    else:
        st.success("✅ OpenAI API Key configured")
        if st.button("🔄 Change API Key"):
            if 'openai_key' in st.session_state:
                del st.session_state['openai_key']
            st.rerun()
        st.divider()
    
    # Initialize AI Filter (will use fallback if no API key)
    ai_filter = AIFilter(config)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload Excel file with firms data",
        type=['xlsx', 'xls'],
        help="Excel file should contain firm information"
    )
    
    if uploaded_file is not None:
        try:
            # Process Excel file
            df = processor.process_excel(uploaded_file)
            st.success(f"✅ Loaded {len(df)} firms from Excel")
            
            # Display sample data
            with st.expander("📊 Sample Data"):
                st.dataframe(df.head())
            
            # Heuristics input
            st.subheader("🎯 Enter Filtering Heuristics")
            heuristics = st.text_area(
                "Describe what you're looking for in firms:",
                placeholder="e.g., 'Looking for AI/ML startups with revenue >$1M, Series A stage, B2B focus'",
                height=100
            )
            
            # Filter button
            if st.button("🔍 Filter Top 10 Firms", type="primary"):
                if heuristics.strip():
                    # Check if API key is available
                    if not openai_key:
                        st.warning("⚠️ No API key configured - Using basic keyword matching fallback")
                    
                    with st.spinner("Analyzing firms..." if openai_key else "Using keyword matching..."):
                        results = ai_filter.filter_firms(df, heuristics)
                        
                        if results:
                            st.subheader("🏆 Top 10 Matching Firms")
                            if not openai_key:
                                st.info("💡 Add an OpenAI API key above for AI-powered filtering with better accuracy")
                            
                            for i, firm in enumerate(results, 1):
                                with st.container():
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.markdown(f"**{i}. {firm['name']}**")
                                        st.markdown(f"📋 **Reason:** {firm['reason']}")
                                    with col2:
                                        st.markdown(f"**Score: {firm['score']:.1f}%**")
                                    st.divider()
                        else:
                            st.warning("No matching firms found. Try adjusting your heuristics.")
                else:
                    st.warning("Please enter heuristics to filter firms")
                    
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    
    # Sidebar info
    with st.sidebar:
        st.markdown("### 📋 How It Works")
        st.markdown("""
        1. **Enter your OpenAI API Key** (at the top)
        2. **Upload Excel file** with firm data
        3. **Enter heuristics** describing your criteria
        4. **Click Filter** to get top 10 matches
        """)
        
        st.markdown("### 🔧 Excel File Format")
        st.markdown("""
        Your Excel file should include these columns:
        
        - **name** - Firm name
        - **description** - Business description
        - **stage** - Funding stage
        - **revenue** - Revenue info
        - **industry** - Industry sector
        - **location** - Company location
        """)
        
        st.markdown("### 🔑 API Key Info")
        st.markdown("""
        - Get your key from [OpenAI Platform](https://platform.openai.com/api-keys)
        - Your key is stored in session only
        - Never shared or logged
        - Works without API key (basic matching)
        """)

if __name__ == "__main__":
    main()
