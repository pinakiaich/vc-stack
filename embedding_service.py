"""
Embedding Service for Vector-Based Semantic Search
Supports both OpenAI embeddings (cloud) and sentence-transformers (local)
"""
import logging
from typing import List, Optional, Union
import numpy as np
from config import Config
from cache_service import CacheService

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingService:
    """Service for generating embeddings for semantic search"""
    
    def __init__(self, config: Config, use_openai: bool = True, cache_service: Optional[CacheService] = None):
        """
        Initialize embedding service
        
        Args:
            config: Configuration object
            use_openai: If True, use OpenAI embeddings (requires API key). 
                       If False, use sentence-transformers (local, free)
            cache_service: Optional cache service for caching embeddings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.use_openai = use_openai
        self.client = None
        self.model = None
        self.cache_service = cache_service
        
        if use_openai and OPENAI_AVAILABLE:
            api_key = config.get_openai_key()
            if api_key:
                self.client = OpenAI(api_key=api_key)
                self.logger.info("Using OpenAI embeddings (cloud-based)")
            else:
                self.logger.warning("OpenAI API key not found, falling back to sentence-transformers")
                use_openai = False
        
        if not use_openai:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                # Use a lightweight, fast model for embeddings
                # all-MiniLM-L6-v2 is fast and works well for semantic search
                try:
                    self.model = SentenceTransformer('all-MiniLM-L6-v2')
                    self.logger.info("Using sentence-transformers (local, free)")
                except Exception as e:
                    self.logger.error(f"Failed to load sentence-transformers model: {e}")
                    raise
            else:
                raise ImportError(
                    "Neither OpenAI nor sentence-transformers available. "
                    "Install with: pip install openai sentence-transformers"
                )
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text string
        
        Args:
            text: Text to embed
            
        Returns:
            numpy array of embedding vector
        """
        # Check cache first
        if self.cache_service:
            cached_embedding = self.cache_service.get_embedding(text)
            if cached_embedding is not None:
                self.logger.debug(f"Cache hit for embedding: {text[:50]}...")
                return cached_embedding
        
        # Generate embedding
        if self.use_openai and self.client:
            embedding = self._embed_openai(text)
        else:
            embedding = self._embed_local(text)
        
        # Cache the result
        if self.cache_service:
            self.cache_service.set_embedding(text, embedding)
        
        return embedding
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a batch of texts (more efficient)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        # Check cache for all texts
        if self.cache_service:
            cached_embeddings, missing_texts = self.cache_service.get_embeddings_batch(texts)
            
            # If all were cached, return them
            if not missing_texts:
                self.logger.debug(f"Cache hit for all {len(texts)} embeddings")
                return np.array([e for e in cached_embeddings if e is not None])
            
            # If some were cached, generate only missing ones
            if len(missing_texts) < len(texts):
                self.logger.debug(f"Cache hit for {len(texts) - len(missing_texts)}/{len(texts)} embeddings")
                # Generate missing embeddings
                if self.use_openai and self.client:
                    missing_embeddings = self._embed_batch_openai(missing_texts)
                else:
                    missing_embeddings = self._embed_batch_local(missing_texts)
                
                # Cache the new embeddings
                self.cache_service.set_embeddings_batch(missing_texts, missing_embeddings)
                
                # Combine cached and new embeddings
                result_embeddings = []
                missing_idx = 0
                for i, text in enumerate(texts):
                    if cached_embeddings[i] is not None:
                        result_embeddings.append(cached_embeddings[i])
                    else:
                        result_embeddings.append(missing_embeddings[missing_idx])
                        missing_idx += 1
                
                return np.array(result_embeddings)
        
        # No cache or all missing - generate all
        if self.use_openai and self.client:
            embeddings = self._embed_batch_openai(texts)
        else:
            embeddings = self._embed_batch_local(texts)
        
        # Cache all results
        if self.cache_service:
            self.cache_service.set_embeddings_batch(texts, embeddings.tolist())
        
        return embeddings
    
    def _embed_openai(self, text: str) -> np.ndarray:
        """Generate embedding using OpenAI API"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",  # Fast and cheap
                input=text
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            self.logger.error(f"OpenAI embedding error: {e}")
            raise
    
    def _embed_batch_openai(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for batch using OpenAI API"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]
            return np.array(embeddings)
        except Exception as e:
            self.logger.error(f"OpenAI batch embedding error: {e}")
            raise
    
    def _embed_local(self, text: str) -> np.ndarray:
        """Generate embedding using sentence-transformers (local)"""
        if not self.model:
            raise RuntimeError("SentenceTransformer model not loaded")
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def _embed_batch_local(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for batch using sentence-transformers (local)"""
        if not self.model:
            raise RuntimeError("SentenceTransformer model not loaded")
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        # Test with a dummy text
        test_embedding = self.embed_text("test")
        return len(test_embedding)
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1, where 1 is most similar)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    @staticmethod
    def cosine_similarity_batch(query_vec: np.ndarray, document_vecs: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarity between query vector and batch of document vectors
        
        Args:
            query_vec: Query vector (1D array)
            document_vecs: Document vectors (2D array, shape: n_docs x embedding_dim)
            
        Returns:
            1D array of similarity scores
        """
        # Normalize vectors
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        doc_norms = document_vecs / (np.linalg.norm(document_vecs, axis=1, keepdims=True) + 1e-8)
        
        # Dot product
        similarities = np.dot(doc_norms, query_norm)
        return similarities
