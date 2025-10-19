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
    
    # Advanced options for data processing
    with st.expander("⚙️ Advanced Options"):
        st.markdown("**Skip Metadata Rows**")
        skip_rows = st.number_input(
            "Number of rows to skip at the top",
            min_value=0,
            max_value=50,
            value=0,
            help="Use this if you see metadata like 'Downloaded on:', 'Created for:' in results"
        )
        st.caption("💡 The app auto-detects metadata. Only change this if results look wrong.")
        
        st.divider()
        
        # Column mapping will be available after file upload
        if 'uploaded_columns' in st.session_state and st.session_state.uploaded_columns:
            st.markdown("**Manual Column Mapping**")
            st.caption("If company names aren't detected correctly, select the right column:")
            
            name_column = st.selectbox(
                "Which column contains company names?",
                options=['Auto-detect'] + st.session_state.uploaded_columns,
                help="Select the column that has company names"
            )
            
            if name_column != 'Auto-detect':
                st.session_state['manual_name_column'] = name_column
            elif 'manual_name_column' in st.session_state:
                del st.session_state['manual_name_column']
    
    if uploaded_file is not None:
        try:
            # Process Excel file
            df = processor.process_excel(uploaded_file, skip_rows=skip_rows)
            
            # Store original columns for manual mapping
            st.session_state.uploaded_columns = [col for col in df.columns if col not in ['name', 'description', 'industry', 'stage', 'revenue', 'location']]
            if len(st.session_state.uploaded_columns) == 0:
                st.session_state.uploaded_columns = df.columns.tolist()
            
            # Apply manual column mapping if set
            if 'manual_name_column' in st.session_state and st.session_state.manual_name_column in df.columns:
                df['name'] = df[st.session_state.manual_name_column]
                st.info(f"ℹ️ Using '{st.session_state.manual_name_column}' as company name column")
            
            # Clean rows with empty or invalid names
            rows_before = len(df)
            df = processor.clean_empty_names(df)
            rows_removed = rows_before - len(df)
            
            if rows_removed > 0:
                st.info(f"ℹ️ Removed {rows_removed} rows with invalid/empty company names")
            
            # Validate that we have actual company data
            if len(df) == 0:
                st.error("❌ No valid company data found in Excel file. Please check your file format.")
                st.stop()
            
            # Check if data looks like company information
            first_names = df['name'].head(5).tolist()
            if all(len(str(name)) < 5 or str(name).isdigit() for name in first_names):
                st.warning("⚠️ The data doesn't look like company names. Try using 'Manual Column Mapping' in Advanced Options.")
            
            st.success(f"✅ Loaded {len(df)} firms from Excel")
            
            # Display sample data and data quality info
            with st.expander("📊 View Uploaded Data (Click to expand)", expanded=True):
                st.markdown("**🔍 Column Detection:**")
                
                # Show which columns were detected/mapped
                detected_cols = {}
                for col in ['name', 'description', 'industry', 'stage', 'revenue']:
                    if col in df.columns:
                        if len(df) > 0 and df[col].iloc[0] != '' and df[col].iloc[0] != 'nan':
                            detected_cols[col] = 'Found ✓'
                        else:
                            detected_cols[col] = 'Empty'
                    else:
                        detected_cols[col] = 'Not found'
                
                col_status1, col_status2 = st.columns(2)
                with col_status1:
                    for key in ['name', 'description', 'industry']:
                        status = "✅" if detected_cols[key] == 'Found ✓' else ("⚠️" if detected_cols[key] == 'Empty' else "❌")
                        st.text(f"{status} {key}: {detected_cols[key]}")
                with col_status2:
                    for key in ['stage', 'revenue']:
                        status = "✅" if detected_cols[key] == 'Found ✓' else ("⚠️" if detected_cols[key] == 'Empty' else "❌")
                        st.text(f"{status} {key}: {detected_cols[key]}")
                
                st.divider()
                
                st.markdown("**📋 All Columns in Your File:**")
                st.code(", ".join(df.columns.tolist()))
                
                st.markdown("**📄 First 5 rows of your data:**")
                st.dataframe(df.head(), use_container_width=True)
                
                st.markdown("**📊 Data Quality:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rows", len(df))
                with col2:
                    non_empty_desc = df[df['description'] != ''].shape[0]
                    st.metric("With Description", non_empty_desc)
                with col3:
                    non_empty_ind = df[df['industry'] != ''].shape[0]
                    st.metric("With Industry", non_empty_ind)
                
                # Warning if data looks problematic
                if len(df) > 0 and 'name' in df.columns:
                    first_name = str(df['name'].iloc[0])
                    if first_name == '' or first_name == 'nan' or len(first_name) < 3:
                        st.error("⚠️ **Problem Detected:** First company name is empty or too short!")
                        st.markdown("**Possible fixes:**")
                        st.markdown("1. Use 'Manual Column Mapping' in Advanced Options above")
                        st.markdown("2. Adjust 'Skip metadata rows' in Advanced Options")
                        st.markdown("3. Make sure your Excel has a 'Company Name' or 'Name' column")
                        st.markdown("4. Check column names in 'All Columns' list below")
            
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
                        st.info("ℹ️ Using basic keyword matching (no API key). Results ranked by keyword matches.")
                    else:
                        st.info("🎯 Using VC Expert Agent - Professional investment analysis")
                    
                    with st.spinner("VC Expert analyzing firms..." if openai_key else "Matching keywords..."):
                        try:
                            results = ai_filter.filter_firms(df, heuristics)
                            
                            if results and len(results) > 0:
                                st.subheader("🏆 Top Matching Firms")
                                
                                # Show filtering method used
                                if openai_key:
                                    st.success("✨ **VC Expert Analysis Complete** - Results analyzed by AI with venture capital expertise")
                                else:
                                    st.info("💡 **Tip:** Add an OpenAI API key above for VC Expert analysis with professional investment reasoning")
                                
                                # Show keywords being searched (only for keyword mode)
                                keywords = [w for w in heuristics.lower().split() if len(w) > 2]
                                if keywords and not openai_key:
                                    st.caption(f"🔍 Searching for keywords: {', '.join(keywords)}")
                                
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
                                st.warning("⚠️ No results returned. This might be due to:")
                                st.markdown("""
                                - Empty or invalid Excel file
                                - No firms in the uploaded data
                                - Technical error in processing
                                
                                **Try:**
                                1. Check the "View Uploaded Data" section above
                                2. Verify your Excel file has data
                                3. Simplify your heuristics (use fewer keywords)
                                """)
                        except Exception as e:
                            st.error(f"❌ Error during filtering: {str(e)}")
                            st.markdown("**Debugging info:**")
                            st.code(f"Error type: {type(e).__name__}\nError message: {str(e)}")
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
