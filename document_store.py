"""
Document Vector Store for RAG (Retrieval-Augmented Generation)
Stores and retrieves document chunks for context injection
"""
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from embedding_service import EmbeddingService
from document_ingestion import DocumentIngestionService

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class DocumentStore:
    """Vector store for document chunks with RAG retrieval"""
    
    def __init__(self, embedding_service: EmbeddingService):
        """
        Initialize document store
        
        Args:
            embedding_service: EmbeddingService for generating document embeddings
        """
        self.embedding_service = embedding_service
        self.logger = logging.getLogger(__name__)
        
        # Store document chunks with embeddings
        self._chunks: List[Dict] = []  # List of {text, embedding, metadata}
        self._vectors: Optional[np.ndarray] = None  # Stacked embeddings matrix
    
    def add_documents(self, chunks: List[Dict]) -> None:
        """
        Add document chunks to the store
        
        Args:
            chunks: List of chunk dictionaries from DocumentIngestionService
        """
        if not chunks:
            return
        
        # Extract texts for batch embedding
        texts = [chunk['text'] for chunk in chunks]
        
        self.logger.info(f"Generating embeddings for {len(chunks)} document chunks...")
        
        # Generate embeddings in batch
        embeddings = self.embedding_service.embed_batch(texts)
        
        # Combine chunks with embeddings
        for chunk, embedding in zip(chunks, embeddings):
            chunk_with_embedding = {
                'text': chunk['text'],
                'embedding': embedding,
                'metadata': chunk.get('metadata', {}),
                'chunk_index': chunk.get('chunk_index', 0)
            }
            self._chunks.append(chunk_with_embedding)
        
        # Rebuild vectors matrix
        self._rebuild_vectors()
        
        self.logger.info(f"Added {len(chunks)} chunks to document store (total: {len(self._chunks)})")
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """
        Retrieve most relevant document chunks for a query
        
        Args:
            query: Query string (investment criteria or question)
            top_k: Number of top chunks to return
            min_similarity: Minimum similarity threshold (0-1)
            
        Returns:
            List of relevant chunks with text, metadata, and similarity score
        """
        if not self._chunks or self._vectors is None:
            self.logger.warning("Document store is empty")
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        # Calculate cosine similarity with all chunks
        similarities = self.embedding_service.cosine_similarity_batch(
            query_embedding,
            self._vectors
        )
        
        # Get top K indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results with similarity scores
        results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            
            # Filter by minimum similarity
            if similarity < min_similarity:
                continue
            
            chunk = self._chunks[idx].copy()
            chunk['similarity'] = similarity
            results.append(chunk)
        
        self.logger.info(
            f"Retrieved {len(results)} relevant chunks "
            f"(top similarity: {results[0]['similarity']:.3f if results else 0})"
        )
        return results
    
    def format_context(self, chunks: List[Dict], max_chars: int = 2000) -> str:
        """
        Format retrieved chunks into context string for LLM prompt
        
        Args:
            chunks: List of chunks from retrieve()
            max_chars: Maximum characters in formatted context
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return ""
        
        formatted_parts = []
        current_length = 0
        
        for i, chunk in enumerate(chunks):
            text = chunk['text']
            metadata = chunk.get('metadata', {})
            source = metadata.get('filename', metadata.get('source', 'Unknown'))
            similarity = chunk.get('similarity', 0.0)
            
            # Format chunk with metadata
            chunk_text = f"[Source: {source}] {text}"
            
            # Check if adding this chunk would exceed limit
            if current_length + len(chunk_text) > max_chars:
                # Try to fit partial chunk
                remaining = max_chars - current_length - 100  # Reserve for formatting
                if remaining > 100:
                    chunk_text = chunk_text[:remaining] + "..."
                else:
                    break
            
            formatted_parts.append(chunk_text)
            current_length += len(chunk_text) + 10  # +10 for formatting overhead
        
        context = "\n\n---\n\n".join(formatted_parts)
        
        if len(context) > max_chars:
            context = context[:max_chars] + "..."
        
        return context
    
    def clear(self) -> None:
        """Clear all documents from the store"""
        self._chunks = []
        self._vectors = None
        self.logger.info("Document store cleared")
    
    def size(self) -> int:
        """Get number of chunks in the store"""
        return len(self._chunks)
    
    def get_document_summary(self) -> Dict:
        """Get summary of documents in the store"""
        if not self._chunks:
            return {'total_chunks': 0, 'sources': []}
        
        sources = {}
        for chunk in self._chunks:
            metadata = chunk.get('metadata', {})
            source = metadata.get('filename', metadata.get('source', 'Unknown'))
            if source not in sources:
                sources[source] = {
                    'filename': source,
                    'chunks': 0,
                    'doc_type': metadata.get('doc_type', 'unknown')
                }
            sources[source]['chunks'] += 1
        
        return {
            'total_chunks': len(self._chunks),
            'sources': list(sources.values())
        }
    
    def _rebuild_vectors(self) -> None:
        """Rebuild the vectors matrix from chunks"""
        if not self._chunks:
            self._vectors = None
            return
        
        embeddings = [chunk['embedding'] for chunk in self._chunks]
        self._vectors = np.vstack(embeddings)
    
    def generate_insights_summary(
        self, 
        openai_api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        max_chunks_to_analyze: int = 20
    ) -> Optional[List[str]]:
        """
        Generate a 5-point summary of key insights learned from ingested documents
        
        Args:
            openai_api_key: OpenAI API key (if not provided, uses env var)
            model: OpenAI model to use
            max_chunks_to_analyze: Maximum number of chunks to analyze (to stay within token limits)
            
        Returns:
            List of 5 key insight points, or None if generation fails
        """
        if not self._chunks:
            self.logger.warning("No chunks available for summary generation")
            return None
        
        if not OPENAI_AVAILABLE:
            self.logger.warning("OpenAI not available for summary generation")
            return None
        
        try:
            # Sample chunks for analysis (use diverse chunks)
            chunks_to_analyze = min(len(self._chunks), max_chunks_to_analyze)
            
            # Sample evenly across chunks for diversity
            step = max(1, len(self._chunks) // chunks_to_analyze)
            sample_chunks = self._chunks[::step][:chunks_to_analyze]
            
            # Extract text from sample chunks
            sample_texts = [chunk['text'] for chunk in sample_chunks]
            
            # Combine into context (limit total length)
            total_chars = sum(len(text) for text in sample_texts)
            max_context_chars = 8000  # Leave room for prompt and response
            
            if total_chars > max_context_chars:
                # Truncate texts proportionally
                scale = max_context_chars / total_chars
                sample_texts = [text[:int(len(text) * scale)] for text in sample_texts]
            
            context = "\n\n---\n\n".join(sample_texts)
            
            # Build prompt
            prompt = f"""Analyze the following VC best practices and documentation content. 
Extract and summarize the 5 most important insights, principles, or key learnings that this content teaches.

Focus on:
- Investment criteria and evaluation frameworks
- Best practices for deal sourcing and analysis
- Key metrics and benchmarks to consider
- Strategic considerations for VC decision-making
- Important patterns or principles mentioned

Provide exactly 5 key insights, each as a clear, concise bullet point (1-2 sentences each).
Format as a simple list, one insight per line.

Content to analyze:
{context}

5 Key Insights:
"""
            
            # Initialize OpenAI client
            if openai_api_key:
                client = OpenAI(api_key=openai_api_key)
            else:
                # Try to get from environment
                client = OpenAI()
            
            # Generate summary
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing VC documentation and extracting key insights. Provide clear, actionable summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3  # Lower temperature for more consistent summaries
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse the 5 points (split by newlines, remove markers like "1.", "-", etc.)
            lines = [line.strip() for line in result_text.split('\n') if line.strip()]
            
            # Clean up bullet points (remove "1.", "-", "•", etc.)
            cleaned_points = []
            for line in lines[:5]:  # Take first 5
                # Remove common list markers
                for marker in ["1.", "2.", "3.", "4.", "5.", "-", "•", "*"]:
                    if line.startswith(marker):
                        line = line[len(marker):].strip()
                        break
                cleaned_points.append(line)
            
            # Ensure we have exactly 5 points
            while len(cleaned_points) < 5:
                cleaned_points.append("")  # Pad with empty strings if needed
            
            self.logger.info(f"Generated insights summary with {len(cleaned_points)} points")
            return cleaned_points[:5]
            
        except Exception as e:
            self.logger.error(f"Error generating insights summary: {str(e)}")
            return None
