import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from data_processor import ExcelProcessor
from ai_filter import AIFilter
from config import Config
from document_ingestion import DocumentIngestionService
from document_store import DocumentStore
from embedding_service import EmbeddingService
from company_research_agent import CompanyResearchAgent
from research_validation_agent import ResearchValidationAgent
from excel_intelligence_agent import ExcelIntelligenceAgent
from industry_hierarchy_agent import IndustryHierarchyAgent
from data_validation_agent import DataValidationAgent
from enhanced_vc_research_agent import EnhancedVCResearchAgent
from vc_knowledge_training_agent import VCKnowledgeTrainingAgent
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
    
    # VC Knowledge Base Section
    st.markdown("### 🧠 VC Knowledge Base")
    
    # Check if VC knowledge base exists
    vc_knowledge_agent = st.session_state.get('vc_knowledge_agent', None)
    
    if vc_knowledge_agent:
        st.success("✅ VC Knowledge Base Loaded")
        st.caption(f"📚 Knowledge base ready for enhanced research")
    else:
        st.info("ℹ️ VC Knowledge Base not loaded")
        st.caption("Build knowledge base for enhanced research with VC industry context")
        
        if st.button("🔨 Build VC Knowledge Base", help="This will take 10-15 minutes"):
            with st.spinner("🔍 Collecting VC industry knowledge... This may take 10-15 minutes"):
                try:
                    from vc_data_search_agent import VCDataSearchAgent
                    from vc_knowledge_training_agent import VCKnowledgeTrainingAgent
                    from embedding_service import EmbeddingService
                    
                    # Step 1: Search for VC knowledge
                    search_agent = VCDataSearchAgent()
                    knowledge_items = search_agent.collect_vc_knowledge_base(max_items=50)  # Start with 50 for faster testing
                    
                    if knowledge_items:
                        # Step 2: Train knowledge base
                        embedding_service = EmbeddingService(config, use_openai=False)
                        training_agent = VCKnowledgeTrainingAgent(config, embedding_service=embedding_service)
                        stats = training_agent.train_on_vc_data(knowledge_items)
                        
                        # Store in session state
                        st.session_state['vc_knowledge_agent'] = training_agent
                        
                        st.success(f"✅ VC Knowledge Base Built!")
                        st.caption(f"Processed {stats['processed']} items, created {stats['total_chunks']} chunks")
                        st.rerun()
                    else:
                        st.warning("⚠️ No knowledge items collected. Check internet connection.")
                except Exception as e:
                    st.error(f"❌ Error building knowledge base: {e}")
                    st.caption("You can continue without it - standard research will still work")
    
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
            
            # Validate Excel data using Data Validation Agent
            try:
                validation_agent = DataValidationAgent()
                
                # Validate a sample of companies
                sample_size = min(5, len(df))
                validation_results = []
                
                for idx in range(sample_size):
                    company_name = df.iloc[idx].get('name', '')
                    if company_name:
                        company_data = {
                            'name': company_name,
                            'industry': df.iloc[idx].get('industry', ''),
                            'stage': df.iloc[idx].get('stage', ''),
                            'revenue': df.iloc[idx].get('revenue', ''),
                            'description': df.iloc[idx].get('description', ''),
                            'location': df.iloc[idx].get('location', ''),
                        }
                        validation = validation_agent.validate_excel_data(company_data, company_name)
                        validation_results.append({
                            'company': company_name,
                            'validation': validation
                        })
                
                # Show validation summary
                if validation_results:
                    total_valid = sum(1 for r in validation_results if r['validation']['is_valid'])
                    avg_confidence = sum(r['validation']['confidence'] for r in validation_results) / len(validation_results)
                    
                    if total_valid == len(validation_results):
                        st.success(f"✅ Data Quality: {total_valid}/{len(validation_results)} companies validated (Avg confidence: {avg_confidence:.0%})")
                    else:
                        st.warning(f"⚠️ Data Quality: {total_valid}/{len(validation_results)} companies validated (Avg confidence: {avg_confidence:.0%})")
                        with st.expander("🔍 View Validation Details", expanded=False):
                            for result in validation_results:
                                if not result['validation']['is_valid']:
                                    st.markdown(f"**{result['company']}:**")
                                    if result['validation']['issues']:
                                        st.caption(f"Issues: {', '.join(result['validation']['issues'])}")
                                    if result['validation']['missing_fields']:
                                        st.caption(f"Missing: {', '.join(result['validation']['missing_fields'])}")
            except Exception as e:
                st.caption(f"ℹ️ Validation check skipped: {e}")
            
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
                
                # Show which columns were detected/mapped (VC analyst approach - check multiple variations)
                detected_cols = {}
                # Check for standard columns and also look for variations
                # CRITICAL: "First Financing Deal Type 2" is the user-specified column for stage
                columns_to_check = {
                    'name': ['name', 'company', 'companies', 'company name'],
                    'description': ['description', 'desc', 'about', 'summary'],
                    'industry': ['industry', 'sector', 'primary industry', 'vertical'],
                    'stage': ['first financing deal type 2', 'first financing deal type', 'financing deal type', 'deal type', 'stage', 'funding stage'],  # User-specified column FIRST
                    'revenue': ['revenue', 'arr', 'annual revenue', 'sales'],
                    'opportunity_score': ['opportunity score', 'opportunity', 'opportunity_score', 'opp score'],
                    'exit_probability_score': ['exit probability score', 'exit probability', 'exit prob', 'exit_probability_score', 'exit score']
                }
                
                for standard_col, variations in columns_to_check.items():
                    found = False
                    for var in variations:
                        # For "First Financing Deal Type 2", use more flexible matching
                        if standard_col == 'stage' and 'first financing deal type 2' in var.lower():
                            # Try exact match first
                            if var in df.columns:
                                non_empty = (df[var] != '').sum()
                                if non_empty > 0:
                                    detected_cols[standard_col] = f'Found ✓ ({non_empty}/{len(df)} filled) [from "{var}"]'
                                    found = True
                                    break
                            # Try case-insensitive exact match
                            for col in df.columns:
                                if ' '.join(col.lower().split()) == ' '.join(var.lower().split()):
                                    non_empty = (df[col] != '').sum()
                                    if non_empty > 0:
                                        detected_cols[standard_col] = f'Found ✓ ({non_empty}/{len(df)} filled) [from "{col}"]'
                                        found = True
                                        break
                            if found:
                                break
                            # Try contains all keywords
                            for col in df.columns:
                                col_lower = col.lower()
                                if all(keyword in col_lower for keyword in ['first', 'financing', 'deal', 'type', '2']):
                                    non_empty = (df[col] != '').sum()
                                    if non_empty > 0:
                                        detected_cols[standard_col] = f'Found ✓ ({non_empty}/{len(df)} filled) [from "{col}"]'
                                        found = True
                                        break
                            if found:
                                break
                        else:
                            # Check exact match first
                            if var in df.columns:
                                non_empty = (df[var] != '').sum()
                                if non_empty > 0:
                                    detected_cols[standard_col] = f'Found ✓ ({non_empty}/{len(df)} filled) [from "{var}"]'
                                    found = True
                                    break
                                else:
                                    detected_cols[standard_col] = f'Empty (0 filled) [found "{var}" but empty]'
                                    found = True
                                    break
                            # Check case-insensitive partial match
                            else:
                                for col in df.columns:
                                    if var.lower() in col.lower() or col.lower() in var.lower():
                                        non_empty = (df[col] != '').sum()
                                        if non_empty > 0:
                                            detected_cols[standard_col] = f'Found ✓ ({non_empty}/{len(df)} filled) [from "{col}"]'
                                            found = True
                                            break
                                if found:
                                    break
                    if not found:
                        detected_cols[standard_col] = 'Not found'
                
                col_status1, col_status2, col_status3 = st.columns(3)
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
                with col_status3:
                    for key in ['opportunity_score', 'exit_probability_score']:
                        if 'Found ✓' in detected_cols[key]:
                            status = "✅"
                        elif 'Empty' in detected_cols[key]:
                            status = "⚠️"
                        else:
                            status = "❌"
                        # Display with friendly names
                        display_name = key.replace('_', ' ').title()
                        st.text(f"{status} {display_name}: {detected_cols[key]}")
                
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
                                
                                # Show progress indicator
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                # Update progress
                                status_text.text("🔄 Initializing filter...")
                                progress_bar.progress(10)
                                
                                # Filter with progress updates
                                try:
                                    status_text.text("🔍 Analyzing companies (this may take a moment)...")
                                    progress_bar.progress(30)
                                    
                                    results = ai_filter.filter_firms(df, heuristics)
                                    
                                    progress_bar.progress(90)
                                    status_text.text("✅ Filtering complete!")
                                    
                                    # CRITICAL: Store results AND DataFrame in session state so they persist after clicking firm names
                                    # This ensures table NEVER disappears
                                    st.session_state['filter_results'] = results
                                    st.session_state['filter_heuristics'] = heuristics
                                    st.session_state['filter_df'] = df  # Store DataFrame for company data lookup
                                    
                                    progress_bar.progress(100)
                                    # Clear progress indicators after a brief moment
                                    import time
                                    time.sleep(0.5)
                                    progress_bar.empty()
                                    status_text.empty()
                                    
                                    # Show success message
                                    if results and len(results) > 0:
                                        st.success("✅ Filtering complete! Results displayed below.")
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
                                    progress_bar.empty()
                                    status_text.empty()
                                    raise
                            except Exception as e:
                                st.error(f"❌ Error during filtering: {str(e)}")
                                st.markdown("**Debugging info:**")
                                st.code(f"Error type: {type(e).__name__}\nError message: {str(e)}")
                else:
                    st.warning("Please enter heuristics to filter firms")
                    
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
        
        # CRITICAL: Display results section OUTSIDE the filter button block
        # This ensures table ALWAYS shows if stored results exist, even after rerun from button clicks
        stored_results = st.session_state.get('filter_results', [])
        stored_df = st.session_state.get('filter_df', None)
        
        if stored_results and len(stored_results) > 0:
            st.subheader("🏆 Top Matching Firms")
            
            # Initialize Excel Intelligence Agent for smart data extraction
            excel_agent = ExcelIntelligenceAgent()
            
            # Helper function to get company data from DataFrame using intelligent agent
            def get_company_data_from_df(company_name: str, df) -> dict:
                """Extract company data from DataFrame using intelligent agent"""
                try:
                    # Use Excel Intelligence Agent to intelligently extract data
                    extracted_data = excel_agent.extract_company_data(company_name, df)
                    return extracted_data
                except Exception as e:
                    logger.error(f"Error extracting company data: {e}")
                    return {}
            
            # Display results with clickable firm names
            st.markdown("**💡 Click on any firm name below to auto-fill the Deal Workspace form in the sidebar**")
            
            # CRITICAL: ALWAYS use stored results from session state (never use local 'results' variable)
            # This ensures table NEVER disappears after button clicks
            display_results = stored_results
            display_df = stored_df
            
            # Safety check: if no stored DataFrame, show warning
            if display_df is None:
                st.warning("⚠️ DataFrame not available. Please run the filter again.")
            else:
                # Show success message if firm was just selected
                if 'firm_selected_timestamp' in st.session_state:
                    selected_firm_name = st.session_state.get('selected_firm', {}).get('name', '')
                    if selected_firm_name:
                        st.success(f"✅ **{selected_firm_name}** selected! Check sidebar form - it should be auto-filled.")
                
                for i, firm in enumerate(display_results, 1):
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            # Make firm name clickable - use link-style button
                            button_clicked = st.button(
                                f"📌 {firm['name']}",
                                key=f"select_firm_{i}_{hash(firm['name'])}",
                                use_container_width=False,
                                help=f"Click to auto-fill Deal Workspace form with {firm['name']} data"
                            )
                            
                            if button_clicked:
                                # Store selected firm data in session state using intelligent agent
                                company_data = get_company_data_from_df(firm['name'], display_df)
                                
                                # Log what was extracted for debugging
                                if company_data:
                                    found_fields = [k for k, v in company_data.items() if v and v != '']
                                    missing_fields = [k for k, v in company_data.items() if not v or v == '']
                                    
                                    if found_fields:
                                        st.success(f"✅ Extracted from Excel: {', '.join(found_fields)}")
                                    if missing_fields and 'stage' in missing_fields:
                                        # Show available columns to help debug
                                        available_cols = [col for col in display_df.columns if any(keyword in col.lower() for keyword in ['stage', 'round', 'series', 'funding'])]
                                        if available_cols:
                                            st.warning(f"⚠️ Stage not found. Excel columns that might contain stage: {', '.join(available_cols[:5])}")
                                        else:
                                            st.info(f"ℹ️ Stage column not found in Excel. Available columns: {', '.join(list(display_df.columns)[:10])}")
                                
                                # Extract stage with fallback
                                extracted_stage = company_data.get('stage', '')
                                
                                # Parse industry hierarchy for better classification
                                extracted_industry = company_data.get('industry', '')
                                extracted_vertical = company_data.get('vertical', '')
                                extracted_description = company_data.get('description', '')
                                
                                try:
                                    hierarchy_agent = IndustryHierarchyAgent()
                                    hierarchy = hierarchy_agent.parse_industry_hierarchy(
                                        extracted_industry, 
                                        extracted_vertical, 
                                        extracted_description
                                    )
                                    
                                    # Store full hierarchy for research
                                    industry_full = hierarchy.get('industry_full', extracted_industry)
                                except Exception:
                                    industry_full = extracted_industry
                                
                                st.session_state['selected_firm'] = {
                                    'name': firm['name'],
                                    'sector': company_data.get('sector', company_data.get('industry', '')),
                                    'industry': extracted_industry,
                                    'industry_full': industry_full,  # Store full hierarchy
                                    'vertical': extracted_vertical,
                                    'stage': extracted_stage,  # Explicitly set stage
                                    'description': extracted_description,
                                    'location': company_data.get('location', ''),
                                    'revenue': company_data.get('revenue', ''),
                                    'opportunity_score': company_data.get('opportunity_score', ''),
                                    'exit_probability_score': company_data.get('exit_probability_score', ''),
                                    'score': firm.get('score', 0),
                                    'reason': firm.get('reason', '')
                                }
                                
                                # Debug: Show what's being stored
                                if extracted_stage:
                                    st.caption(f"📊 Stage extracted: '{extracted_stage}'")
                                else:
                                    st.caption(f"⚠️ Stage not found in Excel for {firm['name']}")
                                # Store timestamp for UI feedback
                                st.session_state['firm_selected_timestamp'] = datetime.now()
                                # Force form to re-render by clearing form submission flag
                                for key in list(st.session_state.keys()):
                                    if key.startswith('create_deal_form_') and key.endswith('_submitted'):
                                        del st.session_state[key]
                                st.rerun()  # Rerun to update form
                            
                            st.markdown(f"📋 **Reason:** {firm['reason']}")
                        with col2:
                            st.markdown(f"**Score: {firm['score']:.1f}%**")
                        st.divider()
    
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
                
                # Initialize research agent and validation agent
                # Initialize research agents
                research_agent = CompanyResearchAgent(config)
                # Ensure research agent has OpenAI key from Streamlit session
                if openai_key and not research_agent.openai_key:
                    research_agent.openai_key = openai_key
                
                validation_agent = ResearchValidationAgent(config)
                data_validation_agent = DataValidationAgent()
                
                # Auto-trigger research if deal was just created
                trigger_research = st.session_state.get('trigger_research', False)
                if trigger_research and deal_id == st.session_state.get('deal_id'):
                    # Clear the trigger
                    st.session_state['trigger_research'] = False
                    refresh_research = True
                else:
                    # Research button or display existing research
                    if existing_research:
                        st.info("✅ Research already conducted. Click 'Refresh Research' to update.")
                        refresh_research = st.button("🔄 Refresh Research", type="primary", key="refresh_research_btn")
                    else:
                        refresh_research = st.button("🔍 Conduct Research", type="primary", key="conduct_research_btn")
                
                if refresh_research:
                    with st.spinner("🔍 Researching company information from internet..."):
                        try:
                            # Get Excel data for the company
                            excel_df = st.session_state.get('filter_df', None)
                            excel_data = {}
                            
                            if excel_df is not None:
                                try:
                                    excel_agent = ExcelIntelligenceAgent()
                                    excel_data = excel_agent.extract_company_data(deal['name'], excel_df)
                                except Exception as e:
                                    st.caption(f"ℹ️ Could not extract Excel data: {e}")
                            
                            # Prepare additional info from deal and Excel
                            additional_info = {
                                'industry': deal.get('sector', excel_data.get('industry', '')),
                                'description': excel_data.get('description', ''),
                            }
                            
                            # Enhance with Excel data
                            if excel_data.get('sector'):
                                additional_info['sector'] = excel_data['sector']
                            if excel_data.get('stage'):
                                additional_info['stage'] = excel_data['stage']
                            if excel_data.get('vertical'):
                                additional_info['vertical'] = excel_data['vertical']
                            
                            # Parse industry hierarchy
                            try:
                                hierarchy_agent = IndustryHierarchyAgent()
                                hierarchy = hierarchy_agent.parse_industry_hierarchy(
                                    additional_info.get('industry', ''),
                                    additional_info.get('vertical', ''),
                                    additional_info.get('description', '')
                                )
                                additional_info['industry_full'] = hierarchy.get('industry_full', '')
                                additional_info['industry_specific'] = hierarchy.get('industry_specific', '')
                                additional_info['industry_niche'] = hierarchy.get('industry_niche', '')
                            except Exception:
                                pass
                            
                            # Try to use Enhanced VC Research Agent if VC knowledge base is available
                            use_enhanced = False
                            
                            try:
                                # Check if VC knowledge base exists (stored in session state)
                                vc_knowledge_agent = st.session_state.get('vc_knowledge_agent', None)
                                
                                if vc_knowledge_agent:
                                    # Use enhanced research agent
                                    enhanced_research_agent = EnhancedVCResearchAgent(config, vc_knowledge_agent=vc_knowledge_agent)
                                    if openai_key:
                                        # Ensure OpenAI key is set
                                        enhanced_research_agent.base_research_agent.openai_key = openai_key
                                    
                                    research_data = enhanced_research_agent.research_company_comprehensive(
                                        company_name=deal['name'],
                                        excel_data=excel_data,
                                        additional_info=additional_info
                                    )
                                    use_enhanced = True
                                    st.success("✅ Using Enhanced VC Research (with VC knowledge base)")
                            except Exception as e:
                                st.caption(f"ℹ️ Enhanced research not available, using standard research: {e}")
                            
                            # Fallback to standard research agent
                            if not use_enhanced:
                                # Ensure research agent has OpenAI key from session state
                                if not research_agent.openai_key and openai_key:
                                    research_agent.openai_key = openai_key
                                
                                # Conduct standard research
                                research_data = research_agent.research_company(deal['name'], additional_info)
                                
                                # Add validation metadata (basic)
                                research_data['_validation'] = {
                                    'excel_validation': None,
                                    'cross_check': None,
                                    'filled_data': None,
                                }
                            
                            # Cross-check Excel vs Research data
                            if excel_data and research_data:
                                try:
                                    cross_check = data_validation_agent.cross_check_data(
                                        excel_data, 
                                        research_data, 
                                        deal['name']
                                    )
                                    
                                    # Store cross-check results
                                    research_data['_cross_check'] = cross_check
                                    
                                    # Show cross-check results
                                    if cross_check.get('discrepancies'):
                                        st.warning(f"⚠️ Found {len(cross_check['discrepancies'])} data discrepancies")
                                        with st.expander("🔍 View Discrepancies", expanded=False):
                                            for disc in cross_check['discrepancies']:
                                                st.markdown(f"**{disc['field']}:**")
                                                st.caption(f"Excel: {disc['excel']}")
                                                st.caption(f"Research: {disc['research']}")
                                                st.caption(f"💡 {disc['recommendation']}")
                                    
                                    if cross_check.get('matches'):
                                        st.success(f"✅ {len(cross_check['matches'])} fields match between Excel and Research")
                                    
                                except Exception as e:
                                    st.caption(f"ℹ️ Cross-check skipped: {e}")
                            
                            # Validate research completeness (if not already validated by enhanced agent)
                            if not use_enhanced or '_validation' not in research_data or 'quality_score' not in research_data.get('_validation', {}):
                                validation = validation_agent.validate_research(research_data, deal['name'])
                                
                                # Show validation results
                                if validation['is_complete']:
                                    st.success(f"✅ Research Complete: {validation['complete_fields']}/{validation['total_fields']} fields populated")
                                else:
                                    quality_pct = validation['quality_score'] * 100
                                    st.warning(f"⚠️ Research Incomplete: {validation['complete_fields']}/{validation['total_fields']} fields ({quality_pct:.0f}% complete)")
                                    
                                    if validation['missing_fields']:
                                        st.error(f"❌ Missing fields: {', '.join(validation['missing_fields'])}")
                                    if validation['empty_fields']:
                                        st.warning(f"⚠️ Empty/Incomplete fields: {', '.join(validation['empty_fields'])}")
                                    
                                    if validation['recommendations']:
                                        with st.expander("💡 Recommendations to Improve Research", expanded=True):
                                            for rec in validation['recommendations']:
                                                st.markdown(f"• {rec}")
                                
                                # Store validation in research data
                                if '_validation' not in research_data:
                                    research_data['_validation'] = {}
                                research_data['_validation']['research_validation'] = validation
                            
                            # Save research findings to database
                            # Format quantitative data for storage
                            quantitative_data = research_data.get('quantitative_data', {})
                            quant_data_text = ""
                            if quantitative_data:
                                quant_lines = []
                                for key, value in quantitative_data.items():
                                    if value and value != "Not available":
                                        label = key.replace('_', ' ').title()
                                        quant_lines.append(f"{label}: {value}")
                                if quant_lines:
                                    quant_data_text = "\n".join(quant_lines)
                            
                            findings_to_save = [
                                {
                                    'category': 'company_info',
                                    'source_type': 'agent_analysis',
                                    'content': f"Company Name: {research_data.get('company_name', 'N/A')}\nCountry of Incorporation: {research_data.get('country_of_incorporation', 'N/A')}\nIndustry: {research_data.get('industry', 'N/A')}",
                                    'citation': 'Internet research via Company Research Agent'
                                },
                                {
                                    'category': 'quantitative_data',
                                    'source_type': 'agent_analysis',
                                    'content': quant_data_text if quant_data_text else 'No quantitative data found',
                                    'citation': 'Internet research via Company Research Agent (Enhanced Search Queries)'
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
                            
                            # Store in session state for display (with validation metadata)
                            # Only add research validation if not already enhanced validation
                            if '_validation' not in research_data or not isinstance(research_data.get('_validation'), dict) or 'excel_validation' not in research_data.get('_validation', {}):
                                research_data['_validation'] = validation
                            st.session_state[f'research_data_{deal_id}'] = research_data
                            st.success("✅ Research completed! Scroll down to see results.")
                            # Don't rerun here - let it display results immediately
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
                    
                    # Show enhanced validation if available
                    enhanced_validation = research_data.get('_validation', {})
                    cross_check = research_data.get('_cross_check', {})
                    
                    # Show Excel validation if available
                    excel_validation = enhanced_validation.get('excel_validation')
                    if excel_validation:
                        confidence = excel_validation.get('confidence', 0)
                        if confidence > 0.7:
                            st.success(f"✅ Excel Data Quality: {confidence:.0%} confidence")
                        elif confidence > 0.5:
                            st.warning(f"⚠️ Excel Data Quality: {confidence:.0%} confidence")
                        else:
                            st.error(f"❌ Excel Data Quality: {confidence:.0%} confidence")
                        
                        if excel_validation.get('issues'):
                            with st.expander("🔍 Excel Data Issues", expanded=False):
                                for issue in excel_validation['issues']:
                                    st.caption(f"• {issue}")
                    
                    # Show cross-check results
                    if cross_check:
                        if cross_check.get('matches'):
                            st.success(f"✅ {len(cross_check['matches'])} fields match between Excel and Research")
                        if cross_check.get('discrepancies'):
                            st.warning(f"⚠️ {len(cross_check['discrepancies'])} discrepancies found")
                            with st.expander("🔍 View Discrepancies", expanded=False):
                                for disc in cross_check['discrepancies']:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown(f"**Excel:** {disc['excel']}")
                                    with col2:
                                        st.markdown(f"**Research:** {disc['research']}")
                                    st.caption(f"💡 {disc['recommendation']}")
                    
                    # Show standard validation status if available
                    validation = research_data.get('_validation', {})
                    if validation and not excel_validation:  # Only show if not already shown
                        quality_pct = validation.get('quality_score', 0) * 100
                        if validation.get('is_complete', False):
                            st.success(f"✅ Research Quality: {quality_pct:.0f}% Complete ({validation.get('complete_fields', 0)}/{validation.get('total_fields', 0)} fields)")
                        else:
                            st.warning(f"⚠️ Research Quality: {quality_pct:.0f}% Complete ({validation.get('complete_fields', 0)}/{validation.get('total_fields', 0)} fields)")
                    
                    # Company Information
                    with st.expander("🏢 Company Information", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            company_name = research_data.get('company_name', 'N/A')
                            country = research_data.get('country_of_incorporation', 'N/A')
                            st.markdown(f"**Company Name:** {company_name}")
                            st.markdown(f"**Country of Incorporation:** {country}")
                        with col2:
                            industry = research_data.get('industry', 'N/A')
                            st.markdown(f"**Industry:** {industry}")
                    
                    # Quantitative Data Section (NEW)
                    quantitative_data = research_data.get('quantitative_data', {})
                    if quantitative_data and any(v != "Not available" and v for v in quantitative_data.values()):
                        with st.expander("📊 Quantitative Data", expanded=True):
                            st.markdown("**Key Metrics & Market Data**")
                            
                            # Market Size Metrics
                            col1, col2 = st.columns(2)
                            with col1:
                                tam = quantitative_data.get('market_size_tam', 'Not available')
                                sam = quantitative_data.get('market_size_sam', 'Not available')
                                if tam and tam != "Not available":
                                    st.metric("📈 Market Size (TAM)", tam)
                                if sam and sam != "Not available":
                                    st.metric("📊 Serviceable Market (SAM)", sam)
                            
                            with col2:
                                cagr = quantitative_data.get('market_growth_cagr', 'Not available')
                                market_share = quantitative_data.get('market_share', 'Not available')
                                if cagr and cagr != "Not available":
                                    st.metric("📈 Market Growth (CAGR)", cagr)
                                if market_share and market_share != "Not available":
                                    st.metric("📊 Market Share", market_share)
                            
                            st.divider()
                            
                            # Company Metrics
                            col3, col4 = st.columns(2)
                            with col3:
                                revenue = quantitative_data.get('company_revenue', 'Not available')
                                funding = quantitative_data.get('funding_raised', 'Not available')
                                if revenue and revenue != "Not available":
                                    st.metric("💰 Revenue", revenue)
                                if funding and funding != "Not available":
                                    st.metric("💵 Funding Raised", funding)
                            
                            with col4:
                                valuation = quantitative_data.get('valuation', 'Not available')
                                employees = quantitative_data.get('employee_count', 'Not available')
                                if valuation and valuation != "Not available":
                                    st.metric("💎 Valuation", valuation)
                                if employees and employees != "Not available":
                                    st.metric("👥 Employees", employees)
                            
                            # Show all quantitative data in a table for reference
                            # Use markdown instead of nested expander (Streamlit doesn't allow nested expanders)
                            st.divider()
                            st.markdown("**📋 All Quantitative Data**")
                            quant_table_data = []
                            for key, value in quantitative_data.items():
                                if value and value != "Not available":
                                    label = key.replace('_', ' ').title()
                                    quant_table_data.append({"Metric": label, "Value": value})
                            
                            if quant_table_data:
                                import pandas as pd
                                quant_df = pd.DataFrame(quant_table_data)
                                st.dataframe(quant_df, use_container_width=True, hide_index=True)
                            else:
                                st.info("No quantitative data available. Enhanced search queries are working, but specific numbers weren't found in search results.")
                    else:
                        with st.expander("📊 Quantitative Data", expanded=False):
                            st.info("💡 Quantitative data extraction is enabled. Numbers will appear here when found in search results.")
                            st.caption("Enhanced search queries are targeting: market size, growth rates, revenue, funding, and other metrics.")
                    
                    # Industry Background
                    industry_bg = research_data.get('industry_background', 'Not available')
                    if industry_bg and industry_bg not in ['Not available', 'Unknown', 'N/A', '']:
                        with st.expander("📈 Industry Background & Growth", expanded=True):
                            st.markdown(industry_bg)
                    else:
                        with st.expander("📈 Industry Background & Growth", expanded=False):
                            st.warning("⚠️ Industry background not available. Research may need to be refreshed.")
                            st.markdown(industry_bg if industry_bg else "Not available")
                    
                    # Company Background
                    company_bg = research_data.get('company_background', 'Not available')
                    if company_bg and company_bg not in ['Not available', 'Unknown', 'N/A', '']:
                        with st.expander("🏛️ Company Background", expanded=True):
                            st.markdown(company_bg)
                    else:
                        with st.expander("🏛️ Company Background", expanded=False):
                            st.warning("⚠️ Company background not available. Research may need to be refreshed.")
                            st.markdown(company_bg if company_bg else "Not available")
                    
                    # Founder Profile
                    founder = research_data.get('founder_profile', 'Not available')
                    if founder and founder not in ['Not available', 'Unknown', 'N/A', '']:
                        with st.expander("👤 Founder Profile", expanded=True):
                            st.markdown(founder)
                    else:
                        with st.expander("👤 Founder Profile", expanded=False):
                            st.warning("⚠️ Founder profile not available. Research may need to be refreshed.")
                            st.markdown(founder if founder else "Not available")
                    
                    # Competition
                    competition = research_data.get('competition', 'Not available')
                    if competition and competition not in ['Not available', 'Unknown', 'N/A', '']:
                        with st.expander("⚔️ Competition & Market Landscape", expanded=True):
                            st.markdown(competition)
                    else:
                        with st.expander("⚔️ Competition & Market Landscape", expanded=False):
                            st.warning("⚠️ Competition analysis not available. Research may need to be refreshed.")
                            st.markdown(competition if competition else "Not available")
                    
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
        
        # Create Deal Form (auto-filled when firm name is clicked)
        # Check if a firm was selected to auto-fill form - read fresh from session state
        selected_firm = st.session_state.get('selected_firm', {})
        expander_expanded = bool(selected_firm)  # Expand if firm is selected
        
        with st.expander("➕ Create New Deal", expanded=expander_expanded):
            if selected_firm:
                firm_name = selected_firm.get('name', 'Unknown')
                st.success(f"✅ **Selected Firm:** {firm_name}")
                if selected_firm.get('sector'):
                    st.caption(f"📊 Sector: {selected_firm.get('sector')}")
                if selected_firm.get('stage'):
                    st.caption(f"📈 Stage: {selected_firm.get('stage')}")
                else:
                    st.warning(f"⚠️ Stage not found in Excel for {firm_name}")
                    # Show available columns to help user
                    excel_df = st.session_state.get('filter_df', None)
                    if excel_df is not None:
                        stage_cols = [col for col in excel_df.columns if any(kw in col.lower() for kw in ['stage', 'round', 'series', 'funding'])]
                        if stage_cols:
                            st.caption(f"💡 Excel columns that might contain stage: {', '.join(stage_cols[:3])}")
                st.info("💡 Form fields below are pre-filled. Review and click 'Create Deal & Start Research' to proceed.")
            
            # CRITICAL: Use unique form key that changes when firm name OR timestamp changes
            # This forces Streamlit to create a completely new form instance with fresh values
            firm_name_for_key = selected_firm.get('name', 'none')
            firm_timestamp = st.session_state.get('firm_selected_timestamp', '')
            # Include timestamp in form key to force re-render when firm is selected
            form_key = f"create_deal_form_{firm_name_for_key}_{str(firm_timestamp)}"
            
            with st.form(form_key, clear_on_submit=False):
                # CRITICAL: Read selected_firm fresh from session state INSIDE the form
                # This ensures we get the latest value after rerun
                current_selected = st.session_state.get('selected_firm', {})
                
                # Auto-fill values from selected firm (intelligently extracted from Excel)
                default_name = current_selected.get('name', '')
                default_sector = current_selected.get('sector', current_selected.get('industry', ''))
                default_stage = current_selected.get('stage', '')
                
                # Debug: Show what was extracted from Excel
                if default_name:
                    extracted_fields = []
                    if default_sector:
                        extracted_fields.append(f"Sector: {default_sector}")
                    if default_stage:
                        extracted_fields.append(f"Stage: {default_stage}")
                    if extracted_fields:
                        st.caption(f"🔍 Auto-filled from Excel: {', '.join(extracted_fields)}")
                    else:
                        st.caption(f"🔍 Company: **{default_name}** (checking Excel for industry/stage...)")
                
                # Form inputs - values will be set from defaults when form re-renders with new key
                # Include timestamp hash in key to force new input instances
                timestamp_hash = hash(str(firm_timestamp)) if firm_timestamp else 0
                deal_name = st.text_input(
                    "Deal Name *", 
                    value=default_name, 
                    key=f"deal_name_{firm_name_for_key}_{timestamp_hash}",
                    help="Name of the investment opportunity (auto-filled when you click a firm name)"
                )
                deal_source = st.text_input(
                    "Source", 
                    value="filter_results", 
                    key=f"deal_source_{firm_name_for_key}",
                    help="How the deal was sourced (e.g., referral, outreach)"
                )
                deal_owner = st.text_input(
                    "Owner", 
                    key=f"deal_owner_{firm_name_for_key}",
                    help="Deal owner/analyst name"
                )
                deal_sector = st.text_input(
                    "Sector *", 
                    value=default_sector, 
                    key=f"deal_sector_{firm_name_for_key}_{timestamp_hash}",
                    help="Industry sector (auto-filled from Excel when you click a firm name - intelligently extracted)"
                )
                deal_stage = st.text_input(
                    "Stage *", 
                    value=default_stage, 
                    key=f"deal_stage_{firm_name_for_key}_{timestamp_hash}",
                    help="Investment stage (auto-filled from Excel when you click a firm name - intelligently extracted)"
                )
                
                # Debug: Show what stage value is being used
                if default_stage:
                    st.caption(f"✅ Stage auto-filled: **{default_stage}**")
                elif default_name:
                    st.caption(f"⚠️ Stage not found in Excel for {default_name}. Please enter manually.")
                
                create_button = st.form_submit_button("Create Deal & Start Research", type="primary")
                
                if create_button:
                    if not deal_name:
                        st.error("Deal name is required")
                    elif not deal_sector or deal_sector.strip() == '':
                        st.warning("⚠️ Sector is recommended. The intelligent agent will try to extract it from Excel if available.")
                        # Continue anyway - let user proceed
                    elif not deal_stage or deal_stage.strip() == '':
                        st.warning("⚠️ Stage is recommended. The intelligent agent will try to extract it from Excel if available.")
                        # Continue anyway - let user proceed
                    
                    if deal_name:
                        try:
                            # Call API to create deal
                            response = requests.post(
                                f"{API_BASE_URL}/v2/deals",
                                json={
                                    "name": deal_name,
                                    "source": deal_source if deal_source else "filter_results",
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
                                
                                # Store deal ID and trigger research
                                st.session_state.deal_id = deal['id']
                                st.session_state['trigger_research'] = True
                                st.session_state['newly_created_deal'] = deal
                                
                                # Clear selected firm
                                if 'selected_firm' in st.session_state:
                                    del st.session_state['selected_firm']
                                
                                st.rerun()
                            else:
                                st.error(f"❌ Error creating deal: {response.text}")
                        except requests.exceptions.RequestException as e:
                            st.error("❌ **Backend API Not Running**")
                            st.markdown("""
                            **The FastAPI backend is not running. Please start it:**
                            
                            1. **Open a new terminal window**
                            2. **Run this command:**
                            ```bash
                            cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
                            uvicorn app.main:app --reload --port 8000
                            ```
                            3. **Keep that terminal running**
                            4. **Come back here and click 'Create Deal & Start Research' again**
                            
                            See `BACKEND_REQUIRED.md` for detailed instructions.
                            """)
                            st.caption(f"Technical error: {str(e)}")
        
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
