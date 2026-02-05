"""
Vector Store for efficient similarity search
Simple in-memory implementation using numpy and cosine similarity
"""
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
from embedding_service import EmbeddingService


class VectorStore:
    """In-memory vector store for fast similarity search"""
    
    def __init__(self, embedding_service: EmbeddingService):
        """
        Initialize vector store
        
        Args:
            embedding_service: EmbeddingService instance for generating embeddings
        """
        self.embedding_service = embedding_service
        self.logger = logging.getLogger(__name__)
        self._vectors: Optional[np.ndarray] = None
        self._metadata: List[Dict] = []  # Store original firm data with each vector
        self._texts: List[str] = []  # Store text representations for debugging
    
    def add_firms(self, firms: List[Dict]) -> None:
        """
        Add firms to the vector store
        
        Args:
            firms: List of firm dictionaries with their data
        """
        if not firms:
            return
        
        # Build text representation for each firm
        firm_texts = [self._build_firm_text(firm) for firm in firms]
        
        # Generate embeddings in batch (more efficient)
        self.logger.info(f"Generating embeddings for {len(firms)} firms...")
        embeddings = self.embedding_service.embed_batch(firm_texts)
        
        # Store vectors and metadata
        if self._vectors is None:
            self._vectors = embeddings
        else:
            self._vectors = np.vstack([self._vectors, embeddings])
        
        self._metadata.extend(firms)
        self._texts.extend(firm_texts)
        
        self.logger.info(f"Added {len(firms)} firms to vector store (total: {len(self._metadata)})")
    
    def search(self, query_text: str, top_k: int = 50) -> List[Tuple[Dict, float]]:
        """
        Search for most similar firms using semantic similarity
        
        Args:
            query_text: Search query (user criteria/heuristics)
            top_k: Number of top results to return
            
        Returns:
            List of tuples (firm_dict, similarity_score) sorted by relevance
        """
        if self._vectors is None or len(self._vectors) == 0:
            self.logger.warning("Vector store is empty")
            return []
        
        # Generate embedding for query
        query_embedding = self.embedding_service.embed_text(query_text)
        
        # Calculate cosine similarity with all firms
        similarities = self.embedding_service.cosine_similarity_batch(
            query_embedding, 
            self._vectors
        )
        
        # Get top K indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results with scores
        results = [
            (self._metadata[idx], float(similarities[idx]))
            for idx in top_indices
        ]
        
        self.logger.info(f"Vector search returned {len(results)} results (top similarity: {results[0][1]:.3f})")
        return results
    
    def clear(self) -> None:
        """Clear all vectors from the store"""
        self._vectors = None
        self._metadata = []
        self._texts = []
        self.logger.info("Vector store cleared")
    
    def size(self) -> int:
        """Get number of firms in the store"""
        return len(self._metadata) if self._metadata else 0
    
    def _build_firm_text(self, firm: Dict) -> str:
        """
        Build a comprehensive text representation of a firm for embedding
        
        This text should include all relevant fields that matter for matching
        
        Args:
            firm: Firm dictionary with various fields
            
        Returns:
            Combined text string representing the firm
        """
        parts = []
        
        # Add name (high weight - repeat it to emphasize)
        name = str(firm.get('name', '')).strip()
        if name and name != 'nan':
            parts.append(name)
            parts.append(name)  # Repeat for emphasis
        
        # Add description
        description = str(firm.get('description', '')).strip()
        if description and description != 'nan' and len(description) > 10:
            parts.append(description)
        
        # Add industry/sector
        industry = str(firm.get('industry', '')).strip()
        if industry and industry != 'nan':
            parts.append(f"Industry: {industry}")
        
        # Add stage
        stage = str(firm.get('stage', '')).strip()
        if stage and stage != 'nan':
            parts.append(f"Stage: {stage}")
        
        # Add revenue
        revenue = str(firm.get('revenue', '')).strip()
        if revenue and revenue != 'nan':
            parts.append(f"Revenue: {revenue}")
        
        # Add location
        location = str(firm.get('location', '')).strip()
        if location and location != 'nan':
            parts.append(f"Location: {location}")
        
        # Add investors (if available)
        investors = str(firm.get('Active Investors', firm.get('investors', ''))).strip()
        if investors and investors != 'nan' and len(investors) > 3:
            parts.append(f"Investors: {investors}")
        
        # Add business status
        status = str(firm.get('Business Status', '')).strip()
        if status and status != 'nan':
            parts.append(f"Status: {status}")
        
        # Combine all parts
        combined = " ".join(parts)
        
        # Limit length to avoid token limits (keep it reasonable)
        max_length = 1000
        if len(combined) > max_length:
            combined = combined[:max_length] + "..."
        
        return combined
