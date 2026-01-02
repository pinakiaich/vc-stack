import streamlit as st
import pandas as pd
import requests
from data_processor import ExcelProcessor
from ai_filter import AIFilter
from config import Config
from document_ingestion import DocumentIngestionService
from document_store import DocumentStore
from embedding_service import EmbeddingService
from company_research_agent import CompanyResearchAgent
import json

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
    
    # Initialize document store for RAG (if documents are uploaded)
    if 'document_store' not in st.session_state:
        st.session_state.document_store = None
    
    # Initialize deal_id in session state
    if 'deal_id' not in st.session_state:
        st.session_state.deal_id = None
    
    # Initialize AI Filter (will use fallback if no API key)
    ai_filter = AIFilter(config)
    
    # Backend API URL (default to localhost)
    API_BASE_URL = "http://localhost:8000"
    
    # Document Upload Section (for RAG)
    with st.expander("📚 VC Best Practices & Documentation (Optional)", expanded=False):
        st.markdown("""
        **Upload documents or provide websites to enhance analysis:**
        - Investment memos and playbooks (upload files)
        - Best practices and guidelines (upload files or websites)
        - Sector research and thesis documents (upload files or websites)
        - Internal wiki content (upload files or provide URLs)
        - External resources (provide website URLs)
        
        Content will be used to provide context-aware analysis that aligns with your firm's practices.
        """)
        
        # Tabs for file upload vs URL input
        tab1, tab2 = st.tabs(["📄 Upload Files", "🌐 Add Websites"])
        
        with tab1:
            doc_file = st.file_uploader(
                "Upload document (PDF, Markdown, or Text)",
                type=['pdf', 'md', 'txt', 'markdown'],
                help="Upload VC best practices, investment memos, or guidelines",
                key="doc_upload"
            )
            
            if doc_file is not None:
                if st.button("📥 Ingest Document", key="ingest_doc"):
                    try:
                        with st.spinner(f"Processing {doc_file.name}..."):
                            import tempfile
                            import os
                            
                            # Initialize document ingestion service
                            doc_ingestion = DocumentIngestionService()
                            
                            # Create temporary file
                            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(doc_file.name)[1]) as tmp_file:
                                tmp_file.write(doc_file.getvalue())
                                tmp_path = tmp_file.name
                            
                            try:
                                # Ingest document
                                chunks = doc_ingestion.ingest_file(tmp_path, metadata={'uploaded_by': 'user', 'source_type': 'file'})
                                
                                if chunks:
                                    # Initialize embedding service and document store if needed
                                    if st.session_state.document_store is None:
                                        embedding_service = EmbeddingService(config, use_openai=False, cache_service=ai_filter.cache_service)
                                        st.session_state.document_store = DocumentStore(embedding_service)
                                    
                                    # Add chunks to document store
                                    st.session_state.document_store.add_documents(chunks)
                                    
                                    # Set document store in hybrid filter
                                    if hasattr(ai_filter, 'hybrid_filter') and ai_filter.hybrid_filter:
                                        ai_filter.hybrid_filter.set_document_store(st.session_state.document_store)
                                    
                                    st.success(f"✅ Ingested {doc_file.name}: {len(chunks)} chunks")
                                    
                                    # Show document summary
                                    summary = st.session_state.document_store.get_document_summary()
                                    st.info(f"📊 Total chunks: {summary['total_chunks']} | Sources: {len(summary['sources'])}")
                                    
                                    # Generate and store insights summary
                                    if config.get_openai_key():
                                        with st.spinner("🧠 Analyzing content and generating key insights..."):
                                            insights = st.session_state.document_store.generate_insights_summary(
                                                openai_api_key=config.get_openai_key()
                                            )
                                            if insights:
                                                st.session_state['document_insights'] = insights
                                    
                                    st.rerun()
                                else:
                                    st.warning("⚠️ No content extracted from document")
                            finally:
                                # Clean up temp file
                                if os.path.exists(tmp_path):
                                    os.unlink(tmp_path)
                                    
                    except Exception as e:
                        st.error(f"❌ Error ingesting document: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        
        with tab2:
            st.markdown("**Enter website URLs to extract content:**")
            st.caption("AI will search and extract relevant content from the provided websites.")
            
            url_input = st.text_input(
                "Website URL",
                placeholder="https://example.com/article or https://your-wiki.com/page",
                help="Enter a URL to extract content from (the page will be scraped and analyzed)",
                key="url_input"
            )
            
            # Store multiple URLs in session state
            if 'ingested_urls' not in st.session_state:
                st.session_state.ingested_urls = []
            
            if url_input:
                if st.button("🔍 Scrape & Add Website", key="scrape_url"):
                    try:
                        with st.spinner(f"Scraping content from {url_input}..."):
                            # Initialize document ingestion service
                            doc_ingestion = DocumentIngestionService()
                            
                            # Ingest URL
                            chunks = doc_ingestion.ingest_url(url_input, metadata={'uploaded_by': 'user', 'source_type': 'url'})
                            
                            if chunks:
                                # Initialize embedding service and document store if needed
                                if st.session_state.document_store is None:
                                    embedding_service = EmbeddingService(config, use_openai=False, cache_service=ai_filter.cache_service)
                                    st.session_state.document_store = DocumentStore(embedding_service)
                                
                                # Add chunks to document store
                                st.session_state.document_store.add_documents(chunks)
                                
                                # Set document store in hybrid filter
                                if hasattr(ai_filter, 'hybrid_filter') and ai_filter.hybrid_filter:
                                    ai_filter.hybrid_filter.set_document_store(st.session_state.document_store)
                                
                                # Track ingested URL
                                st.session_state.ingested_urls.append(url_input)
                                
                                st.success(f"✅ Scraped {url_input}: {len(chunks)} chunks extracted")
                                
                                # Show document summary
                                summary = st.session_state.document_store.get_document_summary()
                                st.info(f"📊 Total chunks: {summary['total_chunks']} | Sources: {len(summary['sources'])}")
                                
                                # Generate and store insights summary
                                if config.get_openai_key():
                                    with st.spinner("🧠 Analyzing content and generating key insights..."):
                                        insights = st.session_state.document_store.generate_insights_summary(
                                            openai_api_key=config.get_openai_key()
                                        )
                                        if insights:
                                            st.session_state['document_insights'] = insights
                                
                                st.rerun()
                            else:
                                st.warning("⚠️ No content extracted from website. The page might be empty or require authentication.")
                    except Exception as e:
                        st.error(f"❌ Error scraping website: {str(e)}")
                        import traceback
                        st.caption("💡 Check the console/terminal for detailed error information")
                        st.code(traceback.format_exc())
            
            # Show ingested URLs
            if st.session_state.ingested_urls:
                st.markdown("**📎 Ingested Websites:**")
                for url in st.session_state.ingested_urls:
                    st.caption(f"• {url}")
                
                if st.button("🗑️ Clear URLs", key="clear_urls"):
                    st.session_state.ingested_urls = []
                    st.rerun()
        
        # Show current documents (from both files and URLs)
        if st.session_state.document_store:
            summary = st.session_state.document_store.get_document_summary()
            if summary['total_chunks'] > 0:
                st.markdown("**📚 Current Knowledge Base:**")
                for source in summary['sources']:
                    source_type = "🌐 Website" if source['doc_type'] == 'web' else "📄 File"
                    st.caption(f"{source_type} • {source['filename']} ({source['chunks']} chunks)")
                
                # Show insights summary if available
                if 'document_insights' in st.session_state and st.session_state.document_insights:
                    st.markdown("---")
                    st.markdown("**🧠 Key Insights Learned:**")
                    st.caption("📋 The following insights have been extracted from your documentation:")
                    for i, insight in enumerate(st.session_state.document_insights, 1):
                        if insight:  # Only show non-empty insights
                            st.markdown(f"**{i}.** {insight}")
                    st.caption("💡 These insights are now incorporated into the AI's analysis framework")
                
                if st.button("🗑️ Clear All Documents", key="clear_all_docs"):
                    st.session_state.document_store.clear()
                    st.session_state.document_store = None
                    st.session_state.ingested_urls = []
                    if 'document_insights' in st.session_state:
                        del st.session_state.document_insights
                    st.rerun()
        
        st.caption("💡 Documents and websites are stored in session. Upload them again after restarting the app.")
    
    st.divider()
    
    # Display selected deal metadata (v2)
    if st.session_state.get('deal_id'):
        try:
            response = requests.get(f"{API_BASE_URL}/v2/deals/{st.session_state.deal_id}", timeout=5)
            if response.status_code == 200:
                deal = response.json()
                st.markdown("### 💼 Active Deal Workspace")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Deal", deal['name'])
                    if deal.get('sector'):
                        st.caption(f"**Sector:** {deal['sector']}")
                with col2:
                    if deal.get('stage'):
                        st.metric("Stage", deal['stage'])
                    if deal.get('owner'):
                        st.caption(f"**Owner:** {deal['owner']}")
                with col3:
                    st.metric("Status", deal.get('status', 'active').title())
                    if deal.get('source'):
                        st.caption(f"**Source:** {deal['source']}")
                st.caption(f"Created: {deal.get('created_at', 'N/A')}")
                st.divider()
            else:
                st.warning(f"⚠️ Could not load deal details: {response.status_code}")
                st.session_state.deal_id = None
        except requests.exceptions.RequestException:
            st.info("💡 FastAPI backend not available - Deal Workspace features disabled")
            st.session_state.deal_id = None
    
    st.divider()
    
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
            st.session_state.uploaded_columns = df.columns.tolist()
            
            # FORCE use "Companies" column (capital C) as the name column
            if 'Companies' in df.columns:
                df['name'] = df['Companies']
                companies_filled = (df['Companies'] != '').sum()
                st.success(f"✅ Auto-selected 'Companies' column ({companies_filled} entries) as company names")
            elif 'companies' in df.columns:
                df['name'] = df['companies']
                companies_filled = (df['companies'] != '').sum()
                st.success(f"✅ Auto-selected 'companies' column ({companies_filled} entries) as company names")
            
            # Apply manual column mapping if set (overrides auto-detection)
            if 'manual_name_column' in st.session_state and st.session_state.manual_name_column in df.columns:
                df['name'] = df[st.session_state.manual_name_column]
                st.info(f"ℹ️ Using '{st.session_state.manual_name_column}' as company name column")
            
            # Clean rows with empty or invalid names
            rows_before = len(df)
            df = processor.clean_empty_names(df)
            rows_removed = rows_before - len(df)
            
            if rows_removed > 0:
                if rows_removed > rows_before * 0.5:
                    st.error(f"⚠️ Removed {rows_removed} out of {rows_before} rows - this seems like too many!")
                    st.warning("The 'name' column might not be detected correctly. Use Manual Column Mapping in Advanced Options.")
                else:
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
                # Show info about data processing
                st.markdown("**📁 File Processing:**")
                st.caption(f"Total rows after processing: {len(df)}")
                if rows_removed > 0:
                    st.caption(f"Rows removed: {rows_removed}")
                st.caption(f"Total columns: {len(df.columns)}")
                
                st.divider()
                
                st.markdown("**🔍 Column Detection:**")
                
                # Show which columns were detected/mapped
                detected_cols = {}
                for col in ['name', 'description', 'industry', 'stage', 'revenue']:
                    if col in df.columns:
                        # Count non-empty values
                        non_empty = (df[col] != '').sum()
                        if non_empty > 0:
                            detected_cols[col] = f'Found ✓ ({non_empty}/{len(df)} filled)'
                        else:
                            detected_cols[col] = 'Empty (0 filled)'
                    else:
                        detected_cols[col] = 'Not found'
                
                col_status1, col_status2 = st.columns(2)
                with col_status1:
                    for key in ['name', 'description', 'industry']:
                        if 'Found ✓' in detected_cols[key]:
                            status = "✅"
                        elif 'Empty' in detected_cols[key]:
                            status = "⚠️"
                        else:
                            status = "❌"
                        st.text(f"{status} {key}: {detected_cols[key]}")
                with col_status2:
                    for key in ['stage', 'revenue']:
                        if 'Found ✓' in detected_cols[key]:
                            status = "✅"
                        elif 'Empty' in detected_cols[key]:
                            status = "⚠️"
                        else:
                            status = "❌"
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
            
            # Show RAG status if documents are loaded
            if st.session_state.get('document_store'):
                summary = st.session_state.document_store.get_document_summary()
                if summary['total_chunks'] > 0:
                    st.info(f"📚 **RAG Active**: {summary['total_chunks']} document chunks loaded. Analysis will incorporate best practices.")
            
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
                        # Show enhanced status with all features
                        status_parts = []
                        
                        if hasattr(ai_filter, 'use_hybrid') and ai_filter.use_hybrid:
                            status_parts.append("⚡ Hybrid Filter")
                            status_parts.append("🔍 Vector Search")
                        
                        if st.session_state.get('document_store'):
                            summary = st.session_state.document_store.get_document_summary()
                            if summary['total_chunks'] > 0:
                                status_parts.append("📚 RAG")
                        
                        if hasattr(ai_filter, 'cache_service') and ai_filter.cache_service:
                            status_parts.append("💾 Cache")
                        
                        if status_parts:
                            st.info(f"{' | '.join(status_parts)} - Enhanced analysis enabled")
                        else:
                            st.info("🎯 Using VC Expert Agent - Professional investment analysis")
                    
                        spinner_text = "Matching keywords..."
                        if openai_key:
                            if hasattr(ai_filter, 'use_hybrid') and ai_filter.use_hybrid:
                                spinner_text = "⚡ Hybrid filter: Vector search + parallel AI analysis..."
                            else:
                                spinner_text = "VC Expert analyzing firms in batches..."
                        
                        with st.spinner(spinner_text):
                            try:
                                # Debug: Check if VC Expert/Hybrid is available
                                if hasattr(ai_filter, 'use_hybrid') and ai_filter.use_hybrid:
                                    vc_available = True  # Hybrid filter handles availability
                                elif hasattr(ai_filter, 'vc_expert'):
                                    vc_available = ai_filter.vc_expert.is_available() if openai_key else False
                                else:
                                    vc_available = False
                                
                                if openai_key and not vc_available:
                                    st.warning("⚠️ VC Expert Agent unavailable - OpenAI package may not be installed. Using keyword matching instead.")
                                    st.caption("Install with: `pip install openai` and restart the app")
                                
                                # Store initial state to detect fallback
                                expected_vc_mode = openai_key and vc_available
                                
                                results = ai_filter.filter_firms(df, heuristics)
                                
                                # Check if results look like fallback (keyword matching)
                                used_fallback = False
                                if results and len(results) > 0:
                                    # Detect fallback by checking if reason is generic
                                    first_reason = results[0].get('reason', '')
                                    if 'mentions' in first_reason.lower() and len(first_reason) < 100:
                                        used_fallback = True
                                
                                if results and len(results) > 0:
                                    st.subheader("🏆 Top Matching Firms")
                                    
                                    # Show cache statistics if available
                                    if hasattr(ai_filter, 'cache_service') and ai_filter.cache_service:
                                        cache_stats = ai_filter.cache_service.get_stats()
                                        cache_hit = cache_stats['result']['hits'] > 0 and cache_stats['result']['misses'] == 0
                                        
                                        if cache_hit:
                                            st.success("⚡ **Results from cache** - Instant results! (No API calls)")
                                        else:
                                            hit_rate = cache_stats['result']['hit_rate']
                                            if hit_rate > 0:
                                                st.info(f"📊 Cache: {cache_stats['result']['hits']} hits / {cache_stats['result']['total']} requests ({hit_rate:.0%} hit rate)")
                                    
                                    # Show ACTUAL filtering method used (detect fallback)
                                    if expected_vc_mode and not used_fallback:
                                        st.success("✨ **VC Expert Analysis Complete** - Results analyzed by AI with venture capital expertise")
                                    elif expected_vc_mode and used_fallback:
                                        st.error("❌ **VC Expert Failed** - Fell back to keyword matching")
                                        
                                        # Show actual error if available
                                        if 'vc_expert_error' in st.session_state:
                                            st.markdown("**Actual Error from OpenAI:**")
                                            st.code(st.session_state['vc_expert_error'])
                                            st.warning("⚠️ Check the terminal/console where Streamlit is running for full error details")
                                            # Don't clear - keep for reference
                                        else:
                                            st.warning("⚠️ **Check the terminal/console** where Streamlit is running - the error details are printed there")
                                    
                                        with st.expander("🔍 Troubleshooting & Diagnosis"):
                                            st.markdown("""
                                            **Common Issues:**
                                            1. **Quota Exceeded**: No OpenAI credits - Add billing at https://platform.openai.com/account/billing
                                            2. **Rate Limit**: Too many requests - Wait a few minutes
                                            3. **Invalid Key**: Generate new key at https://platform.openai.com/api-keys
                                            4. **Network Issue**: Check internet connection
                                            
                                            **Check your usage:** https://platform.openai.com/usage
                                            **Test in Playground:** https://platform.openai.com/playground
                                            
                                            **Check terminal/console** where Streamlit is running for detailed error messages.
                                            """)
                                    elif openai_key and not vc_available:
                                        st.warning("⚠️ **Keyword Matching Mode** - VC Expert unavailable (OpenAI not installed)")
                                        st.info("💡 Install OpenAI: `pip install openai` then restart app for professional VC analysis")
                                    else:
                                        st.info("💡 **Tip:** Add an OpenAI API key above for VC Expert analysis with professional investment reasoning")
                                
                                    # Show keywords being searched (only for keyword mode)
                                    keywords = [w for w in heuristics.lower().split() if len(w) > 2]
                                    if keywords and not openai_key:
                                        st.caption(f"🔍 Searching for keywords: {', '.join(keywords)}")
                                    
                                    # Display results
                                    for i, firm in enumerate(results, 1):
                                        with st.container():
                                            col1, col2 = st.columns([3, 1])
                                            with col1:
                                                st.markdown(f"**{i}. {firm['name']}**")
                                                st.markdown(f"📋 **Reason:** {firm['reason']}")
                                            with col2:
                                                st.markdown(f"**Score: {firm['score']:.1f}%**")
                                            st.divider()
                                    
                                    # Auto-create Deal records for top 10 firms
                                    try:
                                        # Limit to top 10
                                        top_results = results[:10]
                                        
                                        # Create a helper function to find company data in DataFrame
                                        def get_company_data_from_df(company_name: str, df: pd.DataFrame) -> dict:
                                            """Extract company data from DataFrame by name"""
                                            # Try exact match first
                                            match = df[df['name'].str.strip().str.lower() == company_name.strip().lower()]
                                            if match.empty:
                                                # Try partial match
                                                match = df[df['name'].str.strip().str.lower().str.contains(company_name.strip().lower(), na=False, regex=False)]
                                            if not match.empty:
                                                row = match.iloc[0]
                                                return {
                                                    'industry': row.get('industry', ''),
                                                    'sector': row.get('industry', ''),  # Use industry as sector
                                                    'stage': row.get('stage', ''),
                                                    'description': row.get('description', ''),
                                                    'location': row.get('location', ''),
                                                    'revenue': row.get('revenue', ''),
                                                }
                                            return {}
                                        
                                        # Auto-create deals
                                        created_deals = []
                                        for firm in top_results:
                                            company_data = get_company_data_from_df(firm['name'], df)
                                            
                                            deal_payload = {
                                                "name": firm['name'],
                                                "source": "auto-created_from_filter",
                                                "owner": None,
                                                "sector": company_data.get('sector', company_data.get('industry', '')),
                                                "stage": company_data.get('stage', ''),
                                                "status": "active"
                                            }
                                            
                                            try:
                                                response = requests.post(
                                                    f"{API_BASE_URL}/v2/deals",
                                                    json=deal_payload,
                                                    timeout=5
                                                )
                                                if response.status_code == 200:
                                                    deal = response.json()
                                                    created_deals.append(deal)
                                            except requests.exceptions.RequestException:
                                                pass  # Skip if API not available
                                        
                                        if created_deals:
                                            st.success(f"✅ Auto-created {len(created_deals)} deals in Deal Workspace. Check sidebar to select and research.")
                                            # Store created deal IDs in session state for reference
                                            st.session_state['auto_created_deals'] = [d['id'] for d in created_deals]
                                    except Exception as e:
                                        # Silently fail - don't interrupt user flow
                                        pass
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
    
    # Active Deal Workspace Section (Main Content Area)
    if st.session_state.get('deal_id') is not None:
        st.markdown("---")
        st.markdown("## 💼 Active Deal Workspace")
        
        deal_id = st.session_state.deal_id
        try:
            # Fetch deal details
            response = requests.get(f"{API_BASE_URL}/v2/deals/{deal_id}", timeout=5)
            if response.status_code == 200:
                deal = response.json()
                
                # Display deal metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Deal:** {deal['name']}")
                    st.markdown(f"**Sector:** {deal.get('sector', 'N/A')}")
                    st.markdown(f"**Stage:** {deal.get('stage', 'N/A')}")
                with col2:
                    st.markdown(f"**Owner:** {deal.get('owner', 'N/A')}")
                    st.markdown(f"**Status:** {deal.get('status', 'active')}")
                    st.markdown(f"**Source:** {deal.get('source', 'N/A')}")
                with col3:
                    st.markdown(f"**Created:** {deal.get('created_at', 'N/A')}")
                
                st.divider()
                
                # Company Research Section
                st.markdown("### 🔍 Company Research")
                
                # Check if research already exists
                research_response = requests.get(f"{API_BASE_URL}/v2/deals/{deal_id}/research-findings", timeout=5)
                existing_research = {}
                if research_response.status_code == 200:
                    findings = research_response.json()
                    # Group findings by category
                    for finding in findings:
                        category = finding.get('category', 'general')
                        if category not in existing_research:
                            existing_research[category] = []
                        existing_research[category].append(finding)
                
                # Initialize research agent
                research_agent = CompanyResearchAgent(config)
                
                # Research button or display existing research
                if existing_research:
                    st.info("✅ Research already conducted. Click 'Refresh Research' to update.")
                    refresh_research = st.button("🔄 Refresh Research", type="primary")
                else:
                    refresh_research = st.button("🔍 Conduct Research", type="primary")
                
                if refresh_research:
                    with st.spinner("🔍 Researching company information from internet..."):
                        try:
                            # Prepare additional info from deal
                            additional_info = {
                                'industry': deal.get('sector', ''),
                                'description': '',  # Could be enhanced later
                            }
                            
                            # Conduct research
                            research_data = research_agent.research_company(deal['name'], additional_info)
                            
                            # Save research findings to database
                            findings_to_save = [
                                {
                                    'category': 'company_info',
                                    'source_type': 'agent_analysis',
                                    'content': f"Company Name: {research_data.get('company_name', 'N/A')}\nCountry of Incorporation: {research_data.get('country_of_incorporation', 'N/A')}\nIndustry: {research_data.get('industry', 'N/A')}",
                                    'citation': 'Internet research via Company Research Agent'
                                },
                                {
                                    'category': 'industry_background',
                                    'source_type': 'agent_analysis',
                                    'content': research_data.get('industry_background', 'Not available'),
                                    'citation': 'Internet research via Company Research Agent'
                                },
                                {
                                    'category': 'company_background',
                                    'source_type': 'agent_analysis',
                                    'content': research_data.get('company_background', 'Not available'),
                                    'citation': 'Internet research via Company Research Agent'
                                },
                                {
                                    'category': 'founder_profile',
                                    'source_type': 'agent_analysis',
                                    'content': research_data.get('founder_profile', 'Not available'),
                                    'citation': 'Internet research via Company Research Agent'
                                },
                                {
                                    'category': 'competition',
                                    'source_type': 'agent_analysis',
                                    'content': research_data.get('competition', 'Not available'),
                                    'citation': 'Internet research via Company Research Agent'
                                },
                            ]
                            
                            # Save each finding
                            for finding in findings_to_save:
                                try:
                                    requests.post(
                                        f"{API_BASE_URL}/v2/deals/{deal_id}/research-findings",
                                        json={
                                            'deal_id': deal_id,
                                            **finding
                                        },
                                        timeout=5
                                    )
                                except:
                                    pass
                            
                            # Store in session state for display
                            st.session_state[f'research_data_{deal_id}'] = research_data
                            st.success("✅ Research completed!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Research failed: {str(e)}")
                            st.caption("Make sure OpenAI API key is configured and internet connection is available.")
                
                # Display research data (from session state or existing findings)
                research_data = st.session_state.get(f'research_data_{deal_id}')
                if not research_data and existing_research:
                    # Build research_data from existing findings
                    research_data = {
                        'company_name': deal['name'],
                        'country_of_incorporation': '',
                        'industry': deal.get('sector', ''),
                        'industry_background': '',
                        'company_background': '',
                        'founder_profile': '',
                        'competition': ''
                    }
                    for category, findings in existing_research.items():
                        if findings:
                            content = findings[0].get('content', '')
                            if category == 'industry_background':
                                research_data['industry_background'] = content
                            elif category == 'company_background':
                                research_data['company_background'] = content
                            elif category == 'founder_profile':
                                research_data['founder_profile'] = content
                            elif category == 'competition':
                                research_data['competition'] = content
                            elif category == 'company_info':
                                # Parse company info
                                for line in content.split('\n'):
                                    if 'Country of Incorporation:' in line:
                                        research_data['country_of_incorporation'] = line.split(':', 1)[1].strip()
                                    elif 'Industry:' in line:
                                        research_data['industry'] = line.split(':', 1)[1].strip()
                
                if research_data:
                    st.markdown("#### 📊 Research Results")
                    
                    # Company Information
                    with st.expander("🏢 Company Information", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Company Name:** {research_data.get('company_name', 'N/A')}")
                            st.markdown(f"**Country of Incorporation:** {research_data.get('country_of_incorporation', 'N/A')}")
                        with col2:
                            st.markdown(f"**Industry:** {research_data.get('industry', 'N/A')}")
                    
                    # Industry Background
                    with st.expander("📈 Industry Background & Growth", expanded=True):
                        st.markdown(research_data.get('industry_background', 'Not available'))
                    
                    # Company Background
                    with st.expander("🏛️ Company Background", expanded=False):
                        st.markdown(research_data.get('company_background', 'Not available'))
                    
                    # Founder Profile
                    with st.expander("👤 Founder Profile", expanded=False):
                        st.markdown(research_data.get('founder_profile', 'Not available'))
                    
                    # Competition
                    with st.expander("⚔️ Competition & Market Landscape", expanded=False):
                        st.markdown(research_data.get('competition', 'Not available'))
                    
            else:
                st.error(f"❌ Could not fetch deal: {response.status_code}")
        except requests.exceptions.RequestException:
            st.info("💡 Start FastAPI backend to view deal details")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Sidebar info
    with st.sidebar:
        # Deal Workspace (v2) Section
        st.markdown("---")
        st.markdown("### 💼 Deal Workspace (v2)")
        
        # Create Deal Form
        with st.expander("➕ Create New Deal", expanded=False):
            with st.form("create_deal_form"):
                deal_name = st.text_input("Deal Name *", help="Name of the investment opportunity")
                deal_source = st.text_input("Source", help="How the deal was sourced (e.g., referral, outreach)")
                deal_owner = st.text_input("Owner", help="Deal owner/analyst name")
                deal_sector = st.text_input("Sector", help="Industry sector")
                deal_stage = st.text_input("Stage", help="Investment stage (e.g., Series A, Series B)")
                
                create_button = st.form_submit_button("Create Deal", type="primary")
                
                if create_button:
                    if not deal_name:
                        st.error("Deal name is required")
                    else:
                        try:
                            # Call API to create deal
                            response = requests.post(
                                f"{API_BASE_URL}/v2/deals",
                                json={
                                    "name": deal_name,
                                    "source": deal_source if deal_source else None,
                                    "owner": deal_owner if deal_owner else None,
                                    "sector": deal_sector if deal_sector else None,
                                    "stage": deal_stage if deal_stage else None,
                                    "status": "active"
                                },
                                timeout=5
                            )
                            if response.status_code == 200:
                                deal = response.json()
                                st.success(f"✅ Deal '{deal['name']}' created successfully!")
                                st.session_state.deal_id = deal['id']
                                st.rerun()
                            else:
                                st.error(f"❌ Error creating deal: {response.text}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"❌ Could not connect to API: {str(e)}")
                            st.caption("💡 Make sure the FastAPI backend is running (uvicorn app.main:app)")
        
        # Select Deal Dropdown
        try:
            response = requests.get(f"{API_BASE_URL}/v2/deals", timeout=5)
            if response.status_code == 200:
                deals = response.json()
                if deals:
                    deal_options = {f"{d['name']} (ID: {d['id']})": d['id'] for d in deals}
                    deal_option_list = ["-- No deal selected --"] + list(deal_options.keys())
                    
                    # Find current selection index
                    current_index = 0  # Default to "-- No deal selected --"
                    if st.session_state.deal_id is not None:
                        # Find the deal that matches current session state
                        for label, deal_id in deal_options.items():
                            if deal_id == st.session_state.deal_id:
                                current_index = deal_option_list.index(label)
                                break
                    
                    selected_deal_label = st.selectbox(
                        "Select Deal",
                        options=deal_option_list,
                        index=current_index,
                        help="Select a deal to work with"
                    )
                    
                    if selected_deal_label != "-- No deal selected --":
                        if selected_deal_label in deal_options:
                            selected_deal_id = deal_options[selected_deal_label]
                            if st.session_state.deal_id != selected_deal_id:
                                st.session_state.deal_id = selected_deal_id
                                st.rerun()
                    else:
                        if st.session_state.deal_id is not None:
                            st.session_state.deal_id = None
                            st.rerun()
                else:
                    st.info("No deals yet. Create one above.")
                    if st.session_state.deal_id is not None:
                        st.session_state.deal_id = None
            else:
                st.warning(f"⚠️ Could not fetch deals: {response.status_code}")
        except requests.exceptions.RequestException:
            # API not available, show info message
            st.info("💡 Start FastAPI backend to use Deal Workspace")
            if st.session_state.deal_id is not None:
                st.session_state.deal_id = None
        
        st.markdown("---")
        
        st.markdown("### 📋 How It Works")
        st.markdown("""
        1. **Enter your OpenAI API Key** (at the top)
        2. **Upload documents** (optional) - VC best practices for RAG
        3. **Upload Excel file** with firm data
        4. **Enter heuristics** describing your criteria
        5. **Click Filter** to get top 10 matches
        """)
        
        st.markdown("### ⚡ Performance Features")
        st.markdown("""
        - **⚡ Hybrid Filter**: Vector search + AI analysis (6-10x faster)
        - **💾 Caching**: Instant results for repeated queries
        - **📚 RAG**: Enhanced analysis with your best practices
        - **🔄 Async Processing**: Parallel batch analysis
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
        
        st.markdown("### 📚 Document Upload (RAG)")
        st.markdown("""
        Upload internal documentation:
        - Investment memos & playbooks
        - Best practices & guidelines
        - Sector research & thesis docs
        
        Documents enhance analysis with your firm's knowledge.
        """)
        
        st.markdown("### 🔑 API Key Info")
        st.markdown("""
        - Get your key from [OpenAI Platform](https://platform.openai.com/api-keys)
        - Your key is stored in session only
        - Never shared or logged
        - Works without API key (basic matching)
        """)
        
        # Show system status
        st.markdown("---")
        st.markdown("### 🔍 System Status")
        
        status_col1, status_col2 = st.columns(2)
        with status_col1:
            if openai_key:
                st.success("✅ API Key")
            else:
                st.warning("⚠️ No API Key")
        
        with status_col2:
            if hasattr(ai_filter, 'use_hybrid') and ai_filter.use_hybrid:
                st.success("✅ Hybrid Filter")
            else:
                st.info("ℹ️ Standard Mode")
        
        if hasattr(ai_filter, 'cache_service') and ai_filter.cache_service:
            cache_stats = ai_filter.cache_service.get_stats()
            total_requests = cache_stats['result']['total']
            if total_requests > 0:
                hit_rate = cache_stats['result']['hit_rate']
                st.info(f"💾 Cache: {hit_rate:.0%} hit rate")
        
        if st.session_state.get('document_store'):
            summary = st.session_state.document_store.get_document_summary()
            if summary['total_chunks'] > 0:
                st.success(f"📚 RAG: {summary['total_chunks']} chunks")

if __name__ == "__main__":
    main()
