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
    
    # Setup API keys if needed
    if not config.setup_api_keys_ui():
        st.stop()
    
    processor = ExcelProcessor()
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
                    with st.spinner("Analyzing firms..."):
                        results = ai_filter.filter_firms(df, heuristics)
                        
                        st.subheader("🏆 Top 10 Matching Firms")
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
                    st.warning("Please enter heuristics to filter firms")
                    
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    
    # Sidebar info
    with st.sidebar:
        st.markdown("### 📋 Instructions")
        st.markdown("""
        1. Upload Excel file with firm data
        2. Enter specific heuristics/criteria
        3. Get top 10 matching firms with reasons
        """)
        
        st.markdown("### 🔧 Supported Excel Columns")
        st.markdown("""
        - **name**: Firm name
        - **description**: Business description
        - **stage**: Funding stage
        - **revenue**: Revenue information
        - **industry**: Industry sector
        - **location**: Company location
        """)

if __name__ == "__main__":
    main()
