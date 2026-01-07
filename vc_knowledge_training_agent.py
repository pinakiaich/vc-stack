"""
VC Knowledge Training Agent
Processes collected VC data to build a knowledge base with embeddings
"""
import logging
from typing import List, Dict, Optional
from document_ingestion import DocumentIngestionService
from document_store import DocumentStore
from embedding_service import EmbeddingService
from config import Config

logger = logging.getLogger(__name__)


class VCKnowledgeTrainingAgent:
    """Agent that processes VC data to build knowledge base"""
    
    def __init__(self, config: Config, embedding_service: Optional[EmbeddingService] = None):
        self.config = config
        self.logger = logger
        self.embedding_service = embedding_service
        
        # Initialize embedding service if not provided
        if not embedding_service:
            from embedding_service import EmbeddingService
            embedding_service = EmbeddingService(config, use_openai=False)  # Use local embeddings
        
        # Initialize document store for VC knowledge
        self.document_store = DocumentStore(embedding_service=embedding_service)
        
        # Initialize document ingestion
        self.ingestion_service = DocumentIngestionService(embedding_service=embedding_service)
    
    def train_on_vc_data(self, vc_knowledge_items: List[Dict]) -> Dict:
        """
        Process VC knowledge items and build knowledge base
        
        Args:
            vc_knowledge_items: List of knowledge items from VCDataSearchAgent
            
        Returns:
            Dict with training statistics
        """
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
        
        return {
            'total_items': len(vc_knowledge_items),
            'processed': processed_count,
            'errors': error_count,
            'total_chunks': len(self.document_store.documents),
        }
    
    def get_vc_context(self, query: str, top_k: int = 5) -> str:
        """
        Retrieve relevant VC knowledge context for a query
        
        Args:
            query: Query string
            top_k: Number of relevant chunks to retrieve
            
        Returns:
            Formatted context string
        """
        try:
            relevant_chunks = self.document_store.retrieve(
                query,
                top_k=top_k,
                min_similarity=0.3
            )
            
            if not relevant_chunks:
                return ""
            
            context_parts = []
            for i, chunk in enumerate(relevant_chunks, 1):
                metadata = chunk.get('metadata', {})
                title = metadata.get('title', metadata.get('source', 'VC Knowledge'))
                url = metadata.get('url', '')
                content = chunk.get('text', chunk.get('content', ''))
                
                context_parts.append(f"\n[VC Knowledge Source {i}: {title}]")
                if url:
                    context_parts.append(f"Source: {url}")
                context_parts.append(f"{content}\n")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            self.logger.error(f"Error retrieving VC context: {e}")
            return ""
