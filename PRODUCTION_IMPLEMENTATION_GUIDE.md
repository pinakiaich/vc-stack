# 🏭 Production Implementation Guide: Step-by-Step

**Purpose**: Detailed implementation guide for upgrading VC-Stack to production-grade

---

## 📦 Phase 1: Core Infrastructure Upgrades

### **Step 1.1: Vector Database Migration (Pinecone)**

#### **Why Pinecone?**
- Fully managed (no ops)
- Automatic scaling
- 99.9% uptime SLA
- Simple API
- Free tier available

#### **Migration Code**

**Current (ChromaDB)**:
```python
from chromadb import PersistentClient
client = PersistentClient(path="./vc_knowledge_db")
collection = client.get_or_create_collection("vc_knowledge")
```

**Production (Pinecone)**:
```python
from pinecone import Pinecone, ServerlessSpec
from pinecone import Index
import os

# Initialize
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create index (one-time)
index_name = "vc-knowledge"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI text-embedding-3-small
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Connect to index
index = pc.Index(index_name)

# Migration script
def migrate_chromadb_to_pinecone():
    """Migrate existing ChromaDB data to Pinecone"""
    # Read from ChromaDB
    chroma_client = PersistentClient(path="./vc_knowledge_db")
    chroma_collection = chroma_client.get_collection("vc_knowledge")
    
    # Get all data
    all_data = chroma_collection.get()
    
    # Prepare for Pinecone
    vectors = []
    for i, (id, embedding, metadata, document) in enumerate(zip(
        all_data['ids'],
        all_data['embeddings'],
        all_data['metadatas'],
        all_data['documents']
    )):
        vectors.append({
            'id': f"chunk_{i}",
            'values': embedding,
            'metadata': {
                **metadata,
                'text': document
            }
        })
    
    # Batch upload to Pinecone
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)
    
    print(f"Migrated {len(vectors)} vectors to Pinecone")
```

#### **Updated DocumentStore**

```python
from pinecone import Pinecone, Index
from typing import List, Dict, Optional
import numpy as np

class ProductionDocumentStore:
    """Production-grade document store using Pinecone"""
    
    def __init__(self, api_key: str, index_name: str = "vc-knowledge"):
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)
        self.embedding_service = None  # Set separately
    
    def add_documents(self, chunks: List[Dict], namespace: Optional[str] = None):
        """Add documents to Pinecone"""
        if not chunks:
            return
        
        # Generate embeddings
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_service.embed_batch(texts)
        
        # Prepare vectors
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vectors.append({
                'id': f"{namespace or 'default'}_{i}_{hash(chunk['text'])}",
                'values': embedding.tolist() if isinstance(embedding, np.ndarray) else embedding,
                'metadata': {
                    **chunk.get('metadata', {}),
                    'text': chunk['text']
                }
            })
        
        # Batch upsert
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            self.index.upsert(vectors=batch, namespace=namespace)
    
    def retrieve(self, query: str, top_k: int = 5, namespace: Optional[str] = None) -> List[Dict]:
        """Retrieve relevant documents"""
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace
        )
        
        # Format results
        chunks = []
        for match in results.matches:
            chunks.append({
                'text': match.metadata.get('text', ''),
                'metadata': {k: v for k, v in match.metadata.items() if k != 'text'},
                'similarity': match.score
            })
        
        return chunks
    
    def size(self, namespace: Optional[str] = None) -> int:
        """Get number of vectors"""
        stats = self.index.describe_index_stats()
        if namespace:
            return stats.namespaces.get(namespace, {}).get('vector_count', 0)
        return stats.total_vector_count
```

---

### **Step 1.2: Document Processing Upgrade (Unstructured.io)**

#### **Why Unstructured.io?**
- Multi-format support (PDF, Word, Excel, PPT, Images)
- Intelligent parsing (tables, headers, lists)
- OCR for scanned documents
- Open source + cloud API
- Best-in-class parsing quality

#### **Installation**
```bash
pip install unstructured[all-docs]
# Or use cloud API
pip install unstructured-client
```

#### **Implementation**

**Current (PyPDF2)**:
```python
import PyPDF2
pdf_reader = PyPDF2.PdfReader(file)
text = ""
for page in pdf_reader.pages:
    text += page.extract_text()
```

**Production (Unstructured.io)**:
```python
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from unstructured.staging.base import elements_to_json

class ProductionDocumentProcessor:
    """Production-grade document processing"""
    
    def __init__(self, use_cloud_api: bool = False):
        self.use_cloud_api = use_cloud_api
        if use_cloud_api:
            from unstructured_client import UnstructuredClient
            self.client = UnstructuredClient(api_key=os.getenv("UNSTRUCTURED_API_KEY"))
    
    def process_file(self, file_path: str, file_type: Optional[str] = None) -> List[Dict]:
        """Process any document format"""
        if self.use_cloud_api:
            # Use cloud API (handles all formats)
            with open(file_path, 'rb') as f:
                elements = self.client.general.partition(
                    files=f,
                    strategy="hi_res",  # High resolution for tables/images
                    extract_tables=True,
                    extract_images_in_pdf=True
                )
        else:
            # Use local processing
            elements = partition(
                filename=file_path,
                strategy="hi_res",
                extract_tables=True,
                extract_images_in_pdf=True
            )
        
        # Intelligent chunking
        chunks = chunk_by_title(
            elements,
            max_characters=1000,
            combine_under_n_chars=500,
            new_after_n_chars=1500
        )
        
        # Convert to structured format
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            processed_chunks.append({
                'text': str(chunk),
                'metadata': {
                    'chunk_index': i,
                    'element_type': chunk.__class__.__name__,
                    'source': file_path,
                    'has_table': hasattr(chunk, 'metadata') and chunk.metadata.get('table', False)
                }
            })
        
        return processed_chunks
    
    def process_url(self, url: str) -> List[Dict]:
        """Process web URL"""
        if self.use_cloud_api:
            elements = self.client.general.partition_url(url=url)
        else:
            elements = partition(url=url)
        
        chunks = chunk_by_title(elements, max_characters=1000)
        return self._format_chunks(chunks, url)
```

**Supported Formats**:
- ✅ PDF (native + scanned)
- ✅ Word (.docx)
- ✅ Excel (.xlsx)
- ✅ PowerPoint (.pptx)
- ✅ Images (PNG, JPG) with OCR
- ✅ HTML
- ✅ Email (.eml)
- ✅ CSV
- ✅ RTF

---

### **Step 1.3: Web Scraping Upgrade (ScraperAPI)**

#### **Why ScraperAPI?**
- Automatic proxy rotation
- CAPTCHA solving
- JavaScript rendering
- Anti-bot bypass
- Simple API
- Good pricing

#### **Implementation**

**Current (DuckDuckGo + requests)**:
```python
from duckduckgo_search import DDGS
results = list(DDGS().text("query"))
```

**Production (ScraperAPI)**:
```python
import requests
import os
from typing import List, Dict, Optional

class ProductionWebScraper:
    """Production-grade web scraping with ScraperAPI"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SCRAPERAPI_KEY")
        self.base_url = "http://api.scraperapi.com"
    
    def scrape_url(self, url: str, render_js: bool = True) -> Optional[Dict]:
        """Scrape a single URL"""
        try:
            response = requests.get(
                self.base_url,
                params={
                    'api_key': self.api_key,
                    'url': url,
                    'render': 'true' if render_js else 'false',
                    'country_code': 'us',
                    'premium': 'true',  # Use premium proxies
                    'session_number': 1  # Sticky session
                },
                timeout=30
            )
            response.raise_for_status()
            
            # Parse HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content
            title = soup.title.string if soup.title else ''
            
            # Remove scripts, styles, etc.
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            content = soup.get_text(separator='\n', strip=True)
            
            return {
                'title': title,
                'url': url,
                'content': content[:50000],  # Limit size
                'source_type': 'scraped'
            }
        except Exception as e:
            self.logger.error(f"Scraping failed for {url}: {e}")
            return None
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search using ScraperAPI SERP"""
        try:
            response = requests.get(
                self.base_url,
                params={
                    'api_key': self.api_key,
                    'url': f'https://www.google.com/search?q={query}',
                    'render': 'true'
                }
            )
            
            # Parse search results
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            for result in soup.select('div.g')[:max_results]:
                title_elem = result.select_one('h3')
                link_elem = result.select_one('a')
                
                if title_elem and link_elem:
                    results.append({
                        'title': title_elem.get_text(),
                        'url': link_elem.get('href', ''),
                        'snippet': result.select_one('.VwiC3b').get_text() if result.select_one('.VwiC3b') else ''
                    })
            
            return results
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
```

---

### **Step 1.4: Advanced RAG with LlamaIndex**

#### **Why LlamaIndex?**
- Purpose-built for RAG
- Advanced retrieval (hybrid, reranking)
- Multiple data connectors
- Query engines (multi-step)
- Agent capabilities

#### **Installation**
```bash
pip install llama-index
pip install llama-index-vector-stores-pinecone
pip install llama-index-embeddings-openai
```

#### **Implementation**

```python
from llama_index import VectorStoreIndex, ServiceContext, StorageContext
from llama_index.vector_stores import PineconeVectorStore
from llama_index.embeddings import OpenAIEmbedding
from llama_index.llms import OpenAI
from llama_index.retrievers import VectorIndexRetriever
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.postprocessor import SimilarityPostprocessor
from llama_index.response_synthesizers import ResponseMode

class ProductionRAGSystem:
    """Production-grade RAG system with LlamaIndex"""
    
    def __init__(self, openai_api_key: str, pinecone_api_key: str):
        # Initialize services
        self.llm = OpenAI(api_key=openai_api_key, model="gpt-4-turbo-preview")
        self.embed_model = OpenAIEmbedding(api_key=openai_api_key)
        
        # Service context
        self.service_context = ServiceContext.from_defaults(
            llm=self.llm,
            embed_model=self.embed_model,
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Pinecone vector store
        from pinecone import Pinecone
        pc = Pinecone(api_key=pinecone_api_key)
        self.vector_store = PineconeVectorStore(
            pinecone_index=pc.Index("vc-knowledge"),
            namespace="default"
        )
        
        # Create index
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            service_context=self.service_context
        )
    
    def add_documents(self, documents: List[str], metadata: List[Dict] = None):
        """Add documents to RAG system"""
        from llama_index import Document
        
        # Create document objects
        doc_objects = []
        for i, doc_text in enumerate(documents):
            doc = Document(
                text=doc_text,
                metadata=metadata[i] if metadata else {}
            )
            doc_objects.append(doc)
        
        # Add to index
        self.index.insert(doc_objects)
    
    def query(self, query: str, top_k: int = 5, use_reranking: bool = True) -> str:
        """Query RAG system with advanced retrieval"""
        # Create retriever
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k * 2 if use_reranking else top_k  # Retrieve more for reranking
        )
        
        # Optional: Add reranking
        postprocessors = []
        if use_reranking:
            from llama_index.postprocessor import SentenceTransformerRerank
            reranker = SentenceTransformerRerank(
                model="cross-encoder/ms-marco-MiniLM-L-6-v2",
                top_n=top_k
            )
            postprocessors.append(reranker)
        else:
            postprocessors.append(SimilarityPostprocessor(similarity_cutoff=0.7))
        
        # Create query engine
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            node_postprocessors=postprocessors,
            response_mode=ResponseMode.COMPACT
        )
        
        # Query
        response = query_engine.query(query)
        return str(response)
    
    def create_multi_collection_rag(self, collections: Dict[str, VectorStoreIndex]):
        """Create RAG system with multiple collections"""
        from llama_index.query_engine import RouterQueryEngine
        from llama_index.tools import QueryEngineTool
        
        # Create query engines for each collection
        tools = []
        for name, index in collections.items():
            query_engine = index.as_query_engine()
            tool = QueryEngineTool.from_defaults(
                query_engine=query_engine,
                description=f"VC {name} documentation and best practices"
            )
            tools.append(tool)
        
        # Create router query engine
        router_query_engine = RouterQueryEngine.from_defaults(tools)
        return router_query_engine
```

---

## 📄 Phase 2: VC Template Generation

### **Step 2.1: Investment Memo Template**

```python
from jinja2 import Template
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime

class VCTemplateGenerator:
    """Generate professional VC documents"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for VC documents"""
        self.styles.add(ParagraphStyle(
            name='VCHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='VCBody',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=6
        ))
    
    def generate_investment_memo(
        self,
        company_data: Dict,
        analysis: Dict,
        output_format: str = 'pdf'
    ) -> str:
        """Generate investment memo in VC format"""
        
        template_content = """
# INVESTMENT MEMO

**Company**: {{company_name}}  
**Date**: {{date}}  
**Stage**: {{stage}}  
**Sector**: {{sector}}  
**Deal Size**: {{deal_size}}

---

## EXECUTIVE SUMMARY

{{executive_summary}}

**Investment Recommendation**: {{recommendation}}  
**Proposed Investment**: {{proposed_investment}}  
**Valuation**: {{valuation}}  
**Ownership**: {{ownership}}%

---

## MARKET OPPORTUNITY

### Market Size
{{market_size}}

### Market Growth
{{market_growth}}

### Competitive Landscape
{{competitive_landscape}}

---

## PRODUCT & TECHNOLOGY

### Product Overview
{{product_overview}}

### Technology & IP
{{technology_ip}}

### Product-Market Fit
{{product_market_fit}}

---

## BUSINESS MODEL

### Revenue Model
{{revenue_model}}

### Unit Economics
{{unit_economics}}

### Go-to-Market Strategy
{{gtm_strategy}}

---

## FINANCIAL ANALYSIS

### Historical Performance
{{historical_performance}}

### Financial Projections
{{financial_projections}}

### Key Metrics
{{key_metrics}}

---

## INVESTMENT THESIS

{{investment_thesis}}

### Key Strengths
{{key_strengths}}

### Key Risks
{{key_risks}}

---

## RECOMMENDATION

{{recommendation_details}}

**Proposed Terms**:
- Investment Amount: {{investment_amount}}
- Valuation: {{valuation}}
- Ownership: {{ownership}}%
- Board Seat: {{board_seat}}
- Liquidation Preference: {{liquidation_preference}}

---

**Prepared by**: {{analyst_name}}  
**Date**: {{date}}
        """
        
        template = Template(template_content)
        memo_content = template.render(
            company_name=company_data.get('name', ''),
            date=datetime.now().strftime('%Y-%m-%d'),
            stage=company_data.get('stage', ''),
            sector=company_data.get('industry', ''),
            deal_size=analysis.get('deal_size', ''),
            executive_summary=analysis.get('executive_summary', ''),
            recommendation=analysis.get('recommendation', ''),
            proposed_investment=analysis.get('proposed_investment', ''),
            valuation=analysis.get('valuation', ''),
            ownership=analysis.get('ownership', ''),
            market_size=analysis.get('market_size', ''),
            market_growth=analysis.get('market_growth', ''),
            competitive_landscape=analysis.get('competitive_landscape', ''),
            product_overview=analysis.get('product_overview', ''),
            technology_ip=analysis.get('technology_ip', ''),
            product_market_fit=analysis.get('product_market_fit', ''),
            revenue_model=analysis.get('revenue_model', ''),
            unit_economics=analysis.get('unit_economics', ''),
            gtm_strategy=analysis.get('gtm_strategy', ''),
            historical_performance=analysis.get('historical_performance', ''),
            financial_projections=analysis.get('financial_projections', ''),
            key_metrics=analysis.get('key_metrics', ''),
            investment_thesis=analysis.get('investment_thesis', ''),
            key_strengths=analysis.get('key_strengths', ''),
            key_risks=analysis.get('key_risks', ''),
            recommendation_details=analysis.get('recommendation_details', ''),
            investment_amount=analysis.get('investment_amount', ''),
            board_seat=analysis.get('board_seat', 'No'),
            liquidation_preference=analysis.get('liquidation_preference', '1x'),
            analyst_name=analysis.get('analyst_name', 'VC Analyst')
        )
        
        if output_format == 'pdf':
            return self._export_to_pdf(memo_content, f"{company_data.get('name', 'company')}_memo.pdf")
        elif output_format == 'word':
            return self._export_to_word(memo_content, f"{company_data.get('name', 'company')}_memo.docx")
        elif output_format == 'markdown':
            return self._export_to_markdown(memo_content, f"{company_data.get('name', 'company')}_memo.md")
        else:
            return memo_content
    
    def _export_to_pdf(self, content: str, filename: str) -> str:
        """Export to PDF"""
        doc = SimpleDocTemplate(filename, pagesize=letter)
        story = []
        
        # Parse markdown-like content and convert to PDF elements
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2*inch))
                continue
            
            if line.startswith('# '):
                story.append(Paragraph(line[2:], self.styles['VCHeading']))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], self.styles['Heading2']))
            elif line.startswith('**') and line.endswith('**'):
                story.append(Paragraph(line, self.styles['Heading3']))
            else:
                story.append(Paragraph(line, self.styles['VCBody']))
        
        doc.build(story)
        return filename
    
    def _export_to_word(self, content: str, filename: str) -> str:
        """Export to Word"""
        from docx import Document
        from docx.shared import Inches
        
        doc = Document()
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('# '):
                doc.add_heading(line[2:], level=1)
            elif line.startswith('## '):
                doc.add_heading(line[3:], level=2)
            else:
                doc.add_paragraph(line)
        
        doc.save(filename)
        return filename
    
    def _export_to_markdown(self, content: str, filename: str) -> str:
        """Export to Markdown"""
        with open(filename, 'w') as f:
            f.write(content)
        return filename
```

---

## 🤖 Phase 3: Advanced Agent Training

### **Step 3.1: Fine-Tuning Setup**

```python
from openai import OpenAI
import json

class VCAgentFineTuner:
    """Fine-tune LLM on VC knowledge"""
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
    
    def prepare_training_data(self, knowledge_base_chunks: List[Dict]) -> List[Dict]:
        """Prepare training data from knowledge base"""
        training_data = []
        
        for chunk in knowledge_base_chunks:
            # Create training example
            training_example = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a VC expert analyst with deep knowledge of venture capital best practices, evaluation criteria, and industry standards."
                    },
                    {
                        "role": "user",
                        "content": f"Based on VC best practices, how should I evaluate a {chunk.get('metadata', {}).get('industry', 'tech')} company at {chunk.get('metadata', {}).get('stage', 'Series A')} stage?"
                    },
                    {
                        "role": "assistant",
                        "content": chunk.get('text', '')
                    }
                ]
            }
            training_data.append(training_example)
        
        return training_data
    
    def create_training_file(self, training_data: List[Dict], filename: str = "vc_training.jsonl"):
        """Create training file in OpenAI format"""
        with open(filename, 'w') as f:
            for example in training_data:
                f.write(json.dumps(example) + '\n')
        return filename
    
    def upload_training_file(self, filename: str):
        """Upload training file to OpenAI"""
        with open(filename, 'rb') as f:
            file = self.client.files.create(
                file=f,
                purpose="fine-tune"
            )
        return file.id
    
    def create_fine_tune_job(self, training_file_id: str, model: str = "gpt-3.5-turbo"):
        """Create fine-tuning job"""
        job = self.client.fine_tuning.jobs.create(
            training_file=training_file_id,
            model=model,
            hyperparameters={
                "n_epochs": 3,
                "batch_size": 4,
                "learning_rate_multiplier": 1.0
            }
        )
        return job
    
    def check_fine_tune_status(self, job_id: str):
        """Check fine-tuning job status"""
        job = self.client.fine_tuning.jobs.retrieve(job_id)
        return {
            'status': job.status,
            'fine_tuned_model': job.fine_tuned_model,
            'trained_tokens': job.trained_tokens
        }
```

---

### **Step 3.2: LlamaIndex Agent with Tools**

```python
from llama_index.agent import OpenAIAgent
from llama_index.tools import QueryEngineTool, FunctionTool
from llama_index.query_engine import RetrieverQueryEngine

class VCAnalystAgent:
    """Advanced VC analyst agent with tool use"""
    
    def __init__(self, rag_system: ProductionRAGSystem):
        self.rag_system = rag_system
        
        # Create tools
        tools = self._create_tools()
        
        # Create agent
        self.agent = OpenAIAgent.from_tools(
            tools=tools,
            system_prompt=self._get_system_prompt(),
            verbose=True
        )
    
    def _create_tools(self) -> List:
        """Create tools for agent"""
        tools = []
        
        # RAG tool for VC best practices
        vc_practices_engine = self.rag_system.index.as_query_engine()
        tools.append(QueryEngineTool.from_defaults(
            query_engine=vc_practices_engine,
            description="VC best practices, evaluation criteria, and industry standards"
        ))
        
        # RAG tool for investment memos
        if hasattr(self.rag_system, 'memos_index'):
            memos_engine = self.rag_system.memos_index.as_query_engine()
            tools.append(QueryEngineTool.from_defaults(
                query_engine=memos_engine,
                description="Historical investment memos and deal analyses"
            ))
        
        # Calculator tool
        def calculate_valuation(revenue: float, multiple: float) -> float:
            """Calculate company valuation"""
            return revenue * multiple
        
        tools.append(FunctionTool.from_defaults(fn=calculate_valuation))
        
        # Market research tool
        def search_market_data(industry: str) -> str:
            """Search for market data"""
            # Integration with market research APIs
            return f"Market data for {industry}"
        
        tools.append(FunctionTool.from_defaults(fn=search_market_data))
        
        return tools
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for agent"""
        return """You are a senior VC analyst with 15+ years of experience.

You have access to:
- VC best practices and evaluation frameworks
- Historical investment memos
- Market research tools
- Financial calculation tools

When analyzing companies:
1. Use VC best practices to guide your evaluation
2. Reference similar deals from historical memos
3. Calculate valuations and metrics accurately
4. Provide data-driven recommendations

Always explain your reasoning and cite sources when possible."""
    
    def analyze_company(self, company_data: Dict, criteria: str) -> Dict:
        """Analyze company using agent"""
        prompt = f"""
Analyze this company against the investment criteria:

Company: {company_data.get('name', '')}
Industry: {company_data.get('industry', '')}
Stage: {company_data.get('stage', '')}
Revenue: {company_data.get('revenue', '')}

Investment Criteria: {criteria}

Provide:
1. Match score (0-100)
2. Detailed analysis
3. Key strengths
4. Key risks
5. Recommendation
        """
        
        response = self.agent.chat(prompt)
        return {
            'analysis': str(response),
            'reasoning': response.sources if hasattr(response, 'sources') else []
        }
```

---

## 🏗️ Phase 4: Production Infrastructure

### **Step 4.1: Multi-Tenant Architecture**

```python
from fastapi import FastAPI, Depends, Header, HTTPException
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from functools import lru_cache

Base = declarative_base()

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True)
    name = Column(String)
    plan = Column(String)  # free, pro, enterprise

# Multi-tenant middleware
def get_tenant_id(x_tenant_id: str = Header(...)) -> str:
    """Extract tenant ID from header"""
    if not x_tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    return x_tenant_id

def get_tenant_db(tenant_id: str = Depends(get_tenant_id)) -> Session:
    """Get database connection for tenant"""
    # Create tenant-specific database connection
    engine = create_engine(f"postgresql://user:pass@host/{tenant_id}_db")
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def get_tenant_vector_store(tenant_id: str = Depends(get_tenant_id)):
    """Get vector store for tenant"""
    from pinecone import Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return pc.Index(f"vc-knowledge-{tenant_id}")

# FastAPI app with tenant isolation
app = FastAPI()

@app.get("/api/v1/companies")
async def get_companies(
    tenant_db: Session = Depends(get_tenant_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Get companies for tenant"""
    # Automatically filtered by tenant
    return {"companies": []}
```

---

### **Step 4.2: Monitoring & Observability**

```python
from datadog import initialize, api
import logging
from functools import wraps
import time

# Initialize Datadog
initialize(api_key=os.getenv("DATADOG_API_KEY"), app_key=os.getenv("DATADOG_APP_KEY"))

def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Log to Datadog
            api.Metric.send(
                metric=f"vc_stack.{func.__name__}.duration",
                points=[(time.time(), duration)],
                tags=[f"function:{func.__name__}"]
            )
            
            return result
        except Exception as e:
            # Log error
            api.Metric.send(
                metric=f"vc_stack.{func.__name__}.error",
                points=[(time.time(), 1)],
                tags=[f"function:{func.__name__}", f"error:{type(e).__name__}"]
            )
            raise
    return wrapper

# Usage
@monitor_performance
def analyze_company(company_data, criteria):
    # Analysis logic
    pass
```

---

## 📊 Cost-Benefit Analysis

### **Tool Comparison Matrix**

| Tool | Free Tier | Starter | Business | Enterprise | Best For |
|------|-----------|---------|----------|------------|----------|
| **Pinecone** | 100K vectors | $70/mo | $200/mo | Custom | Fast deployment |
| **Weaviate** | Self-hosted | $25/mo | $200/mo | Custom | More control |
| **Unstructured.io** | Open source | API: $0.001/page | - | Custom | Multi-format |
| **ScraperAPI** | 1K requests | $49/mo | $249/mo | Custom | Web scraping |
| **OpenAI GPT-4** | - | $0.01/1K tokens | - | - | Best quality |

### **ROI Calculation**

**Investment**: ~$1,500-2,000/month (100 users)
**Benefits**:
- ✅ Professional-grade platform
- ✅ Scalable to 1,000+ users
- ✅ Enterprise-ready
- ✅ Multi-format support
- ✅ Advanced RAG capabilities

**Break-even**: ~$15-20/user/month

---

## 🚀 Quick Start: Production Migration

### **Week 1: Core Upgrades**
1. Set up Pinecone account & index
2. Migrate ChromaDB → Pinecone
3. Test vector search performance

### **Week 2: Document Processing**
1. Integrate Unstructured.io
2. Test multi-format uploads
3. Update document ingestion

### **Week 3: Web Scraping**
1. Set up ScraperAPI account
2. Replace DuckDuckGo search
3. Test scraping reliability

### **Week 4: RAG Framework**
1. Install LlamaIndex
2. Migrate to LlamaIndex RAG
3. Test advanced retrieval

---

## ✅ Summary

**Recommended Stack**:
- **Vector DB**: Pinecone (managed, scalable)
- **Document Processing**: Unstructured.io (multi-format)
- **Web Scraping**: ScraperAPI (production-grade)
- **RAG Framework**: LlamaIndex (advanced)
- **LLM**: OpenAI GPT-4 Turbo
- **Templates**: Jinja2 + ReportLab

**Timeline**: 3-6 months to production
**Cost**: $1,500-2,000/month (100 users)

**Result**: Commercial-grade, scalable, enterprise-ready platform! 🚀
