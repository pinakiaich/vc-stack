"""
VC Knowledge Training Agent
Processes collected VC data to build a knowledge base with embeddings
Supports persistent storage using ChromaDB
"""
import logging
import os
from typing import List, Dict, Optional
from document_ingestion import DocumentIngestionService
from document_store import DocumentStore
from embedding_service import EmbeddingService
from config import Config

logger = logging.getLogger(__name__)


class VCKnowledgeTrainingAgent:
    """Agent that processes VC data to build knowledge base"""
    
    def __init__(self, config: Config, embedding_service: Optional[EmbeddingService] = None, db_path: Optional[str] = None):
        """
        Initialize VC Knowledge Training Agent
        
        Args:
            config: Configuration object
            embedding_service: Optional EmbeddingService (will create if not provided)
            db_path: Optional path to persistent database (default: ./vc_knowledge_db)
        """
        self.config = config
        self.logger = logger
        self.embedding_service = embedding_service
        
        # Initialize embedding service if not provided
        if not embedding_service:
            from embedding_service import EmbeddingService
            embedding_service = EmbeddingService(config, use_openai=False)  # Use local embeddings
        
        # Set default database path if not provided
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "vc_knowledge_db")
        
        self.db_path = db_path
        
        # Initialize document store for VC knowledge with persistence
        self.document_store = DocumentStore(
            embedding_service=embedding_service,
            db_path=db_path,
            collection_name="vc_knowledge"
        )
        
        # Initialize document ingestion
        self.ingestion_service = DocumentIngestionService(embedding_service=embedding_service)
    
    def knowledge_base_exists(self) -> bool:
        """
        Check if knowledge base already exists (has been built)
        
        Returns:
            True if knowledge base exists, False otherwise
        """
        return self.document_store.exists()
    
    def train_on_vc_data(self, vc_knowledge_items: List[Dict], force_rebuild: bool = False) -> Dict:
        """
        Process VC knowledge items and build knowledge base
        
        Args:
            vc_knowledge_items: List of knowledge items from VCDataSearchAgent
            force_rebuild: If True, rebuild even if knowledge base exists
            
        Returns:
            Dict with training statistics
        """
        # Check if knowledge base already exists
        if not force_rebuild and self.knowledge_base_exists():
            self.logger.info("Knowledge base already exists. Use force_rebuild=True to rebuild.")
            return {
                'status': 'skipped',
                'reason': 'already_exists',
                'total_chunks': self.document_store.size(),
                'message': 'Knowledge base already exists. Use force_rebuild=True to rebuild.'
            }
        self.logger.info(f"Training on {len(vc_knowledge_items)} VC knowledge items")
        
        processed_count = 0
        error_count = 0
        
        for item in vc_knowledge_items:
            try:
                # Extract content
                title = item.get('title', 'Untitled')
                content = item.get('content', '')
                url = item.get('url', '')
                source_type = item.get('source_type', 'vc_knowledge')
                
                if not content or len(content) < 100:
                    continue
                
                # Create document metadata
                metadata = {
                    'title': title,
                    'url': url,
                    'source_type': source_type,
                    'query': item.get('query', ''),
                    'category': 'vc_knowledge',
                }
                
                # Ingest as text document
                chunks = self.ingestion_service.ingest_text(
                    content,
                    source_name=title or url,
                    metadata=metadata
                )
                
                # Store chunks in document store
                # DocumentStore expects chunks with 'text' field, not 'content'
                chunks_for_store = []
                for chunk in chunks:
                    chunks_for_store.append({
                        'text': chunk.get('text', chunk.get('content', '')),
                        'metadata': {**metadata, **chunk.get('metadata', {})},
                        'chunk_index': chunk.get('chunk_index', 0)
                    })
                
                # Add all chunks at once
                if chunks_for_store:
                    self.document_store.add_documents(chunks_for_store)
                
                processed_count += 1
                
            except Exception as e:
                self.logger.error(f"Error processing VC knowledge item: {e}")
                error_count += 1
                continue
        
        self.logger.info(f"Training complete: {processed_count} items processed, {error_count} errors")
        
        total_chunks = self.document_store.size()
        self.logger.info(f"Knowledge base saved to {self.db_path} with {total_chunks} chunks")
        
        return {
            'status': 'completed',
            'total_items': len(vc_knowledge_items),
            'processed': processed_count,
            'errors': error_count,
            'total_chunks': total_chunks,
        }
    
    def generate_training_principles(self, max_chunks: int = 50) -> str:
        """
        Generate VC training principles from knowledge base to train the agent
        
        This creates a summary of key VC best practices, evaluation criteria, and principles
        that the agent should learn and apply when analyzing companies.
        
        Args:
            max_chunks: Maximum number of chunks to analyze for training principles
            
        Returns:
            Formatted training principles string for agent system prompt
        """
        if not self.knowledge_base_exists():
            self.logger.warning("Knowledge base does not exist. Build it first.")
            return ""
        
        try:
            # Get a diverse sample of chunks from the knowledge base
            total_chunks = self.document_store.size()
            if total_chunks == 0:
                return ""
            
            # Sample chunks evenly across the knowledge base
            sample_size = min(max_chunks, total_chunks)
            step = max(1, total_chunks // sample_size)
            
            # Get chunks using queries that cover different VC topics
            training_queries = [
                "venture capital evaluation criteria investment analysis",
                "startup valuation methods due diligence process",
                "VC best practices investment thesis",
                "venture capital market analysis benchmarks",
                "investment decision making portfolio company",
            ]
            
            all_chunks = []
            seen_texts = set()
            
            for query in training_queries:
                chunks = self.document_store.retrieve(query, top_k=10, min_similarity=0.2)
                for chunk in chunks:
                    text = chunk.get('text', '')
                    if text and text not in seen_texts:
                        seen_texts.add(text)
                        all_chunks.append(chunk)
                        if len(all_chunks) >= sample_size:
                            break
                if len(all_chunks) >= sample_size:
                    break
            
            if not all_chunks:
                self.logger.warning("No chunks retrieved for training principles")
                return ""
            
            # Use OpenAI to generate training principles summary
            if not self.config.get_openai_key():
                self.logger.warning("OpenAI API key not available. Cannot generate training principles.")
                # Fallback: return key excerpts from chunks
                return self._generate_fallback_principles(all_chunks[:20])
            
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.config.get_openai_key())
                
                # Prepare content for analysis
                content_text = "\n\n---\n\n".join([
                    chunk.get('text', '')[:500]  # Limit each chunk to 500 chars
                    for chunk in all_chunks[:30]  # Use first 30 chunks
                ])
                
                # Generate training principles
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert at analyzing VC documentation and extracting key principles and best practices for training a VC analyst agent."
                        },
                        {
                            "role": "user",
                            "content": f"""Analyze the following VC best practices and documentation. Extract and summarize the key principles, evaluation criteria, and best practices that a VC analyst agent should learn and apply when analyzing companies.

Focus on:
- Investment evaluation criteria and frameworks
- How to assess company-market fit
- Valuation methods and benchmarks
- Due diligence best practices
- Key metrics to consider (revenue, growth, stage, etc.)
- Red flags and risk factors
- What makes a good investment opportunity
- How to structure investment analysis

Provide a concise summary (500-800 words) that can be used to train a VC analyst agent. Format as clear principles and guidelines.

VC Knowledge Base Content:
{content_text}

Training Principles Summary:"""
                        }
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )
                
                principles = response.choices[0].message.content.strip()
                self.logger.info(f"Generated training principles ({len(principles)} chars)")
                return principles
                
            except Exception as e:
                self.logger.error(f"Error generating training principles with OpenAI: {e}")
                # Fallback to simple extraction
                return self._generate_fallback_principles(all_chunks[:20])
                
        except Exception as e:
            self.logger.error(f"Error generating training principles: {e}")
            return ""
    
    def _generate_fallback_principles(self, chunks: List[Dict]) -> str:
        """Generate fallback principles without OpenAI"""
        principles = [
            "## VC Analysis Principles (from Knowledge Base)",
            "",
            "Key principles extracted from VC best practices:",
            ""
        ]
        
        # Extract key phrases and concepts
        key_concepts = set()
        for chunk in chunks:
            text = chunk.get('text', '')
            # Simple extraction of key phrases
            if 'valuation' in text.lower():
                key_concepts.add("Consider valuation methods and benchmarks")
            if 'due diligence' in text.lower():
                key_concepts.add("Perform thorough due diligence")
            if 'market fit' in text.lower() or 'product-market fit' in text.lower():
                key_concepts.add("Evaluate company-market fit")
            if 'growth' in text.lower() and 'revenue' in text.lower():
                key_concepts.add("Assess revenue growth rates")
            if 'stage' in text.lower() and 'funding' in text.lower():
                key_concepts.add("Consider funding stage and milestones")
        
        principles.extend([f"- {concept}" for concept in sorted(key_concepts)])
        return "\n".join(principles)
    
    def get_vc_context(self, query: str, top_k: int = 5) -> str:
        """
        DEPRECATED: Use generate_training_principles() instead
        
        This method was for RAG context injection, but the knowledge base
        should be used for training the agent, not as context.
        """
        self.logger.warning("get_vc_context() is deprecated. Use generate_training_principles() for agent training.")
        return ""
