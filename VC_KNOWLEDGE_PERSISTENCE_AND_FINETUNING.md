# 🧠 VC Knowledge Base: Persistence & Fine-Tuning Strategy

**Problem**: VC knowledge base takes 10-15 minutes to build and is lost on restart. Need persistence and fine-tuning capabilities.

**Current State**:
- ✅ Knowledge collection via web scraping (10-15 min)
- ✅ Document chunking and embedding generation
- ❌ **No persistence** - in-memory only (lost on restart)
- ❌ **No fine-tuning** - only RAG (retrieval), not model training
- ❌ **Rebuilds every time** - slow and inefficient

---

## 🎯 Solution Options Overview

### Option 1: **Persistence Only** (Fastest to implement, lowest cost)
- Save knowledge base to disk
- Load on startup
- Still uses RAG (retrieval), no model training
- **Cost**: $0 (local storage)
- **Time**: 10-15 min once, then instant loads

### Option 2: **Persistence + Incremental Updates** (Recommended for MVP)
- Save knowledge base to disk
- Only update with new content
- Smart caching and change detection
- **Cost**: $0 (local storage)
- **Time**: 10-15 min first time, then 1-2 min for updates

### Option 3: **Persistence + OpenAI Fine-Tuning** (Best quality, higher cost)
- Save knowledge base to disk
- Fine-tune GPT-3.5/GPT-4 on VC knowledge
- Model learns VC best practices
- **Cost**: $0.008-$0.12 per 1K tokens (training) + usage costs
- **Time**: 10-15 min first time, then fine-tuning (hours)

### Option 4: **Persistence + Local Fine-Tuning** (Best control, technical complexity)
- Save knowledge base to disk
- Fine-tune open-source models (Llama, Mistral) locally
- Full control, no API costs
- **Cost**: $0 (but requires GPU)
- **Time**: 10-15 min first time, then fine-tuning (hours, requires GPU)

---

## 📦 Option 1: Persistence Only (RAG with Disk Storage)

### Implementation Approach

**Storage Format Options**:

#### A. **Pickle + NumPy Arrays** (Simplest, Fast)
```python
# Save
import pickle
import numpy as np

knowledge_base = {
    'chunks': chunks,  # List of {text, metadata, chunk_index}
    'embeddings': np.array(embeddings),  # Stacked embeddings matrix
    'metadata': metadata,  # Source info, timestamps
}

with open('vc_knowledge_base.pkl', 'wb') as f:
    pickle.dump(knowledge_base, f)

# Load
with open('vc_knowledge_base.pkl', 'rb') as f:
    knowledge_base = pickle.load(f)
```

**Pros**:
- ✅ Fast to implement (1-2 hours)
- ✅ Fast loading (seconds)
- ✅ Preserves all data structures
- ✅ No external dependencies

**Cons**:
- ❌ Not human-readable
- ❌ Python version dependent
- ❌ Large file size (embeddings are big)

**File Size Estimate**:
- 100 items × 5 chunks/item = 500 chunks
- 500 chunks × 384 dims (sentence-transformers) × 4 bytes = ~750 KB
- Plus text/metadata = ~2-5 MB total

---

#### B. **SQLite + Vector Extension** (Production-ready)
```python
# Use sqlite-vss or chromadb for vector search
import sqlite3
import chromadb

# ChromaDB (recommended)
client = chromadb.PersistentClient(path="./vc_knowledge_db")
collection = client.get_or_create_collection("vc_knowledge")

# Save chunks with embeddings
collection.add(
    documents=[chunk['text'] for chunk in chunks],
    embeddings=[chunk['embedding'] for chunk in chunks],
    metadatas=[chunk['metadata'] for chunk in chunks],
    ids=[f"chunk_{i}" for i in range(len(chunks))]
)

# Load (automatic on query)
results = collection.query(
    query_texts=[query],
    n_results=5
)
```

**Pros**:
- ✅ Production-ready
- ✅ Built-in vector search
- ✅ Incremental updates easy
- ✅ Metadata filtering
- ✅ Human-readable (SQLite)

**Cons**:
- ❌ Requires chromadb dependency
- ❌ Slightly slower than pickle (still fast)

**File Size Estimate**:
- Similar to pickle (~2-5 MB for 100 items)
- Better compression with ChromaDB

---

#### C. **JSON + Separate Embeddings File** (Human-readable)
```python
# Save chunks as JSON
import json
import numpy as np

# Save metadata as JSON
with open('vc_knowledge_metadata.json', 'w') as f:
    json.dump({
        'chunks': [{'text': c['text'], 'metadata': c['metadata']} for c in chunks],
        'version': '1.0',
        'created_at': datetime.now().isoformat(),
    }, f, indent=2)

# Save embeddings as numpy array
np.save('vc_knowledge_embeddings.npy', embeddings)

# Load
with open('vc_knowledge_metadata.json', 'r') as f:
    metadata = json.load(f)
embeddings = np.load('vc_knowledge_embeddings.npy')
```

**Pros**:
- ✅ Human-readable metadata
- ✅ Easy to inspect/debug
- ✅ Version control friendly (JSON)

**Cons**:
- ❌ Two files to manage
- ❌ Slower than pickle
- ❌ Large JSON files

---

### **Recommended: ChromaDB (Option B)**

**Why ChromaDB?**
- ✅ Built for RAG applications
- ✅ Automatic persistence
- ✅ Fast vector search
- ✅ Easy incremental updates
- ✅ Metadata filtering
- ✅ Production-ready

**Implementation Time**: 2-3 hours
**Cost**: $0 (local storage)
**Load Time**: < 1 second

---

## 🎓 Option 2: Persistence + Incremental Updates

### Smart Caching Strategy

```python
class PersistentVCKnowledgeBase:
    def __init__(self, db_path="./vc_knowledge_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection("vc_knowledge")
        self.metadata_store = {}  # Track what's been ingested
    
    def needs_update(self, knowledge_items):
        """Check if any items are new or updated"""
        for item in knowledge_items:
            url = item.get('url', '')
            content_hash = hash(item.get('content', ''))
            
            if url not in self.metadata_store:
                return True  # New item
            if self.metadata_store[url]['hash'] != content_hash:
                return True  # Updated item
        
        return False  # No updates needed
    
    def add_or_update(self, knowledge_items):
        """Only add new/updated items"""
        new_items = []
        for item in knowledge_items:
            url = item.get('url', '')
            content_hash = hash(item.get('content', ''))
            
            if url not in self.metadata_store or \
               self.metadata_store[url]['hash'] != content_hash:
                new_items.append(item)
                self.metadata_store[url] = {
                    'hash': content_hash,
                    'added_at': datetime.now()
                }
        
        if new_items:
            # Process and add only new items
            self._process_and_add(new_items)
```

**Benefits**:
- ✅ First build: 10-15 minutes
- ✅ Subsequent builds: 1-2 minutes (only new content)
- ✅ Automatic deduplication
- ✅ Change detection

**Implementation Time**: 3-4 hours
**Cost**: $0
**Update Time**: 1-2 minutes (only new content)

---

## 🤖 Option 3: Persistence + OpenAI Fine-Tuning

### Fine-Tuning Approach

**What is Fine-Tuning?**
- Train GPT-3.5/GPT-4 on your VC knowledge
- Model learns VC best practices, terminology, evaluation criteria
- Model becomes a "VC expert" without needing RAG context

**Process**:

1. **Prepare Training Data** (from knowledge base):
```python
# Convert knowledge base to fine-tuning format
training_data = []

for chunk in knowledge_chunks:
    # Create training examples
    training_data.append({
        "messages": [
            {
                "role": "system",
                "content": "You are a VC expert analyst with deep knowledge of venture capital best practices, evaluation criteria, and industry standards."
            },
            {
                "role": "user",
                "content": f"Based on VC best practices, how should I evaluate a {chunk['metadata']['industry']} company at {chunk['metadata']['stage']} stage?"
            },
            {
                "role": "assistant",
                "content": chunk['text']  # Knowledge from chunk
            }
        ]
    })
```

2. **Upload to OpenAI**:
```python
from openai import OpenAI

client = OpenAI()

# Upload training file
training_file = client.files.create(
    file=open("vc_training_data.jsonl", "rb"),
    purpose="fine-tune"
)

# Create fine-tuning job
fine_tune_job = client.fine_tuning.jobs.create(
    training_file=training_file.id,
    model="gpt-3.5-turbo",  # or "gpt-4"
    hyperparameters={
        "n_epochs": 3,  # Number of training epochs
    }
)
```

3. **Use Fine-Tuned Model**:
```python
# Use fine-tuned model instead of base model
response = client.chat.completions.create(
    model="ft:gpt-3.5-turbo:your-org:vc-expert:abc123",  # Your fine-tuned model
    messages=[
        {"role": "system", "content": "You are a VC expert analyst."},
        {"role": "user", "content": "Evaluate this startup..."}
    ]
)
```

### Cost Analysis

**Training Costs** (One-time):
- **GPT-3.5-turbo fine-tuning**: $0.008 per 1K tokens
- **GPT-4 fine-tuning**: $0.12 per 1K tokens (much more expensive)

**Example Calculation**:
- 100 knowledge items × 5 chunks/item = 500 chunks
- Average chunk: 200 tokens
- Total: 500 × 200 = 100,000 tokens
- Training epochs: 3
- Total training tokens: 100,000 × 3 = 300,000 tokens

**Costs**:
- GPT-3.5-turbo: 300K tokens × $0.008/1K = **$2.40** (one-time)
- GPT-4: 300K tokens × $0.12/1K = **$36.00** (one-time)

**Usage Costs** (Ongoing):
- Fine-tuned GPT-3.5-turbo: Same as base model ($0.0015/$0.002 per 1K tokens)
- Fine-tuned GPT-4: Same as base model ($0.03/$0.06 per 1K tokens)

**Total Cost Estimate**:
- **One-time training**: $2.40 (GPT-3.5) or $36 (GPT-4)
- **Monthly usage** (assuming 1000 queries/month):
  - GPT-3.5: ~$5-10/month
  - GPT-4: ~$50-100/month

### Pros & Cons

**Pros**:
- ✅ Model learns VC knowledge permanently
- ✅ No need for RAG context (faster inference)
- ✅ Better reasoning (model understands VC domain)
- ✅ Can combine with RAG for best of both worlds

**Cons**:
- ❌ Higher upfront cost ($2-36)
- ❌ Training takes hours (not minutes)
- ❌ Need to retrain when knowledge base updates
- ❌ Model size limits (GPT-3.5: 4K context, GPT-4: 8K/32K)

**Implementation Time**: 1-2 days (data prep + training)
**Best For**: Production use with stable knowledge base

---

## 🔬 Option 4: Persistence + Local Fine-Tuning

### Local Fine-Tuning with Open-Source Models

**Models to Consider**:
- **Llama 2/3** (7B, 13B, 70B) - Meta
- **Mistral 7B** - Mistral AI
- **Phi-2** (2.7B) - Microsoft (smallest, fastest)

**Approach**: LoRA (Low-Rank Adaptation)
- Fine-tune only small adapter layers
- Much faster and cheaper than full fine-tuning
- Can run on consumer GPUs

**Implementation**:
```python
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load base model
model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-v0.1")
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")

# Configure LoRA
lora_config = LoraConfig(
    r=16,  # Rank
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
)

# Apply LoRA
model = get_peft_model(model, lora_config)

# Train on VC knowledge
# ... training code ...
```

### Cost Analysis

**Hardware Requirements**:
- **GPU**: NVIDIA GPU with 8GB+ VRAM (RTX 3060, RTX 4060, etc.)
- **RAM**: 16GB+ system RAM
- **Storage**: 20GB+ for model files

**Costs**:
- **One-time**: GPU purchase ($300-800 for consumer GPU, or cloud GPU rental)
- **Training**: $0 (local) or $0.50-2/hour (cloud GPU rental)
- **Usage**: $0 (runs locally, no API costs)

**Cloud GPU Options**:
- **RunPod**: $0.29/hour (RTX 3090)
- **Vast.ai**: $0.20-0.50/hour (various GPUs)
- **Lambda Labs**: $0.50/hour (A10)

**Training Time**:
- **Mistral 7B + LoRA**: 2-4 hours on RTX 3090
- **Llama 2 7B + LoRA**: 2-4 hours on RTX 3090
- **Phi-2 + LoRA**: 30-60 minutes on RTX 3060

### Pros & Cons

**Pros**:
- ✅ $0 ongoing costs (after GPU purchase)
- ✅ Full control over model
- ✅ Can fine-tune on sensitive/internal data
- ✅ No API rate limits
- ✅ Privacy (data never leaves your machine)

**Cons**:
- ❌ Requires GPU (hardware cost)
- ❌ More complex setup
- ❌ Slower inference than API (unless you have good GPU)
- ❌ Model quality may be lower than GPT-4

**Implementation Time**: 3-5 days (setup + training)
**Best For**: Privacy-sensitive use cases, high-volume usage

---

## 💰 Cost Comparison Summary

| Option | Setup Cost | Training Cost | Monthly Usage | Total (Year 1) |
|-------|-----------|---------------|---------------|----------------|
| **1. Persistence Only** | $0 | $0 | $0 | **$0** |
| **2. Persistence + Updates** | $0 | $0 | $0 | **$0** |
| **3. OpenAI Fine-Tuning** | $0 | $2.40-$36 | $60-$1,200 | **$722-$14,436** |
| **4. Local Fine-Tuning** | $300-$800 (GPU) | $0-$8 (cloud) | $0 | **$300-$808** |

**Assumptions**:
- 1000 queries/month
- GPT-3.5 for Option 3
- Consumer GPU for Option 4

---

## 🎯 Recommended Implementation Plan

### Phase 1: **Persistence (Week 1)** ⭐ START HERE
**Goal**: Eliminate 10-15 minute rebuild time

**Implementation**:
1. Add ChromaDB persistence to `DocumentStore`
2. Save knowledge base after building
3. Load on startup (check if exists)
4. Add "Rebuild" button for manual updates

**Benefits**:
- ✅ Instant startup (no 10-15 min wait)
- ✅ Knowledge base persists across restarts
- ✅ $0 cost
- ✅ Fast to implement (2-3 hours)

**Code Changes**:
- Modify `document_store.py` to use ChromaDB
- Add save/load methods to `VCKnowledgeTrainingAgent`
- Update `streamlit_app.py` to load on startup

---

### Phase 2: **Incremental Updates (Week 2)**
**Goal**: Only update with new content

**Implementation**:
1. Track ingested URLs/content hashes
2. Check for updates before rebuilding
3. Only process new/changed items
4. Merge with existing knowledge base

**Benefits**:
- ✅ 1-2 minute updates (vs 10-15 min full rebuild)
- ✅ Automatic deduplication
- ✅ Change detection

**Code Changes**:
- Add metadata tracking to `VCKnowledgeTrainingAgent`
- Implement `needs_update()` and `add_or_update()` methods
- Update build process to check for changes

---

### Phase 3: **Fine-Tuning (Month 2+)** - Optional
**Goal**: Model learns VC knowledge permanently

**Decision Point**:
- **If high volume** (1000+ queries/month): Consider OpenAI fine-tuning
- **If privacy-sensitive**: Consider local fine-tuning
- **If low volume**: Skip fine-tuning, RAG is sufficient

**Implementation**:
- Prepare training data from knowledge base
- Fine-tune model (OpenAI or local)
- Update agents to use fine-tuned model
- A/B test fine-tuned vs RAG performance

---

## 📝 Implementation Details

### ChromaDB Integration

**File**: `document_store.py`

```python
import chromadb
from chromadb.config import Settings

class PersistentDocumentStore:
    def __init__(self, db_path="./vc_knowledge_db", embedding_service=None):
        self.embedding_service = embedding_service
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="vc_knowledge",
            metadata={"hnsw:space": "cosine"}  # Cosine similarity
        )
    
    def save_knowledge_base(self, chunks):
        """Save chunks to ChromaDB"""
        if not chunks:
            return
        
        # Extract data
        texts = [chunk['text'] for chunk in chunks]
        embeddings = [chunk['embedding'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        ids = [f"chunk_{i}_{hash(chunk['text'])}" for i, chunk in enumerate(chunks)]
        
        # Add to collection
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    def load_knowledge_base(self):
        """Check if knowledge base exists"""
        return self.collection.count() > 0
    
    def retrieve(self, query, top_k=5, min_similarity=0.3):
        """Retrieve relevant chunks"""
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        chunks = []
        for i, doc in enumerate(results['documents'][0]):
            similarity = 1 - results['distances'][0][i]  # Convert distance to similarity
            if similarity >= min_similarity:
                chunks.append({
                    'text': doc,
                    'metadata': results['metadatas'][0][i],
                    'similarity': similarity
                })
        
        return chunks
```

### Update VCKnowledgeTrainingAgent

**File**: `vc_knowledge_training_agent.py`

```python
class VCKnowledgeTrainingAgent:
    def __init__(self, config, embedding_service=None, db_path="./vc_knowledge_db"):
        # ... existing code ...
        
        # Use persistent document store
        self.document_store = PersistentDocumentStore(
            db_path=db_path,
            embedding_service=embedding_service
        )
    
    def knowledge_base_exists(self):
        """Check if knowledge base is already built"""
        return self.document_store.load_knowledge_base()
    
    def train_on_vc_data(self, vc_knowledge_items, force_rebuild=False):
        """Train on VC data, with optional rebuild"""
        if not force_rebuild and self.knowledge_base_exists():
            self.logger.info("Knowledge base already exists. Use force_rebuild=True to rebuild.")
            return {'status': 'skipped', 'reason': 'already_exists'}
        
        # ... existing training code ...
        
        # Save to persistent store
        self.document_store.save_knowledge_base(chunks_for_store)
        
        return stats
```

### Update Streamlit App

**File**: `streamlit_app.py`

```python
# Load VC knowledge base on startup
if 'vc_knowledge_agent' not in st.session_state:
    try:
        from vc_knowledge_training_agent import VCKnowledgeTrainingAgent
        from embedding_service import EmbeddingService
        
        embedding_service = EmbeddingService(config, use_openai=False)
        training_agent = VCKnowledgeTrainingAgent(config, embedding_service=embedding_service)
        
        if training_agent.knowledge_base_exists():
            st.session_state['vc_knowledge_agent'] = training_agent
            st.success("✅ VC Knowledge Base Loaded from disk")
        else:
            st.info("ℹ️ VC Knowledge Base not found. Click 'Build' to create it.")
    except Exception as e:
        st.warning(f"Could not load knowledge base: {e}")

# Build button with rebuild option
if st.button("🔨 Build VC Knowledge Base"):
    force_rebuild = st.checkbox("Force rebuild (ignore existing)", value=False)
    
    with st.spinner("🔍 Building knowledge base..."):
        # ... build code ...
        stats = training_agent.train_on_vc_data(knowledge_items, force_rebuild=force_rebuild)
        
        if stats.get('status') == 'skipped':
            st.info("ℹ️ Knowledge base already exists. Check 'Force rebuild' to rebuild.")
        else:
            st.success(f"✅ Built! Processed {stats['processed']} items")
```

---

## 🚀 Quick Start: Persistence Implementation

**Estimated Time**: 2-3 hours
**Cost**: $0
**Impact**: Eliminates 10-15 minute rebuild time

**Steps**:
1. Install ChromaDB: `pip install chromadb`
2. Update `document_store.py` with ChromaDB persistence
3. Update `vc_knowledge_training_agent.py` to use persistent store
4. Update `streamlit_app.py` to load on startup
5. Test: Build once, restart app, verify instant load

**Files to Modify**:
- `document_store.py` - Add ChromaDB integration
- `vc_knowledge_training_agent.py` - Add save/load methods
- `streamlit_app.py` - Load on startup
- `requirements.txt` - Add `chromadb`

---

## 📊 Decision Matrix

**Choose Option 1 (Persistence Only) if**:
- ✅ You want fastest implementation
- ✅ You want $0 cost
- ✅ RAG quality is sufficient
- ✅ Knowledge base doesn't change often

**Choose Option 2 (Persistence + Updates) if**:
- ✅ Knowledge base updates regularly
- ✅ You want efficient updates
- ✅ You want automatic deduplication

**Choose Option 3 (OpenAI Fine-Tuning) if**:
- ✅ You have budget ($2-36 training + usage)
- ✅ You want best quality reasoning
- ✅ You have high query volume (1000+/month)
- ✅ Knowledge base is stable

**Choose Option 4 (Local Fine-Tuning) if**:
- ✅ You have GPU access
- ✅ Privacy is critical
- ✅ Very high query volume
- ✅ You want $0 ongoing costs

---

## 🎯 Next Steps

1. **Immediate**: Implement Option 1 (Persistence) - 2-3 hours
2. **Week 2**: Add Option 2 (Incremental Updates) - 3-4 hours
3. **Month 2+**: Evaluate fine-tuning based on usage patterns

**Priority**: Start with persistence to eliminate the 10-15 minute wait time!
