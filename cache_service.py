"""
Caching Service for embeddings and analysis results
Provides in-memory caching with optional file-based persistence
"""
import hashlib
import json
import logging
import os
import pickle
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


class CacheService:
    """Service for caching embeddings and analysis results"""
    
    def __init__(
        self, 
        cache_dir: str = ".cache",
        enable_file_persistence: bool = True,
        default_ttl_hours: Optional[int] = None
    ):
        """
        Initialize cache service
        
        Args:
            cache_dir: Directory for file-based cache
            enable_file_persistence: If True, persist cache to disk
            default_ttl_hours: Default TTL in hours (None = no expiration)
        """
        self.cache_dir = cache_dir
        self.enable_file_persistence = enable_file_persistence
        self.default_ttl_hours = default_ttl_hours
        self.logger = logging.getLogger(__name__)
        
        # In-memory caches
        self._embedding_cache: Dict[str, Tuple[np.ndarray, datetime]] = {}
        self._result_cache: Dict[str, Tuple[Any, datetime]] = {}
        self._vector_search_cache: Dict[str, Tuple[List, datetime]] = {}
        
        # Cache statistics
        self.stats = {
            'embedding_hits': 0,
            'embedding_misses': 0,
            'result_hits': 0,
            'result_misses': 0,
            'vector_search_hits': 0,
            'vector_search_misses': 0,
        }
        
        # Create cache directory if needed
        if enable_file_persistence:
            os.makedirs(cache_dir, exist_ok=True)
            self._load_from_disk()
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            MD5 hash of serialized arguments
        """
        # Create a stable string representation
        key_parts = []
        for arg in args:
            if isinstance(arg, (str, int, float, bool, type(None))):
                key_parts.append(str(arg))
            elif isinstance(arg, (list, dict)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            elif isinstance(arg, np.ndarray):
                key_parts.append(str(arg.tobytes()))
            else:
                key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_expired(self, timestamp: datetime, ttl_hours: Optional[int] = None) -> bool:
        """Check if cached item has expired"""
        if ttl_hours is None:
            ttl_hours = self.default_ttl_hours
        
        if ttl_hours is None:
            return False  # No expiration
        
        expiry_time = timestamp + timedelta(hours=ttl_hours)
        return datetime.now() > expiry_time
    
    # Embedding Cache
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get cached embedding for text
        
        Args:
            text: Text to look up
            
        Returns:
            Cached embedding or None if not found/expired
        """
        cache_key = self._get_cache_key("embedding", text)
        
        if cache_key in self._embedding_cache:
            embedding, timestamp = self._embedding_cache[cache_key]
            
            if not self._is_expired(timestamp):
                self.stats['embedding_hits'] += 1
                return embedding
            else:
                # Expired, remove it
                del self._embedding_cache[cache_key]
        
        self.stats['embedding_misses'] += 1
        return None
    
    def set_embedding(self, text: str, embedding: np.ndarray) -> None:
        """
        Cache embedding for text
        
        Args:
            text: Text that was embedded
            embedding: Embedding vector
        """
        cache_key = self._get_cache_key("embedding", text)
        self._embedding_cache[cache_key] = (embedding, datetime.now())
        
        # Persist to disk if enabled
        if self.enable_file_persistence:
            self._save_embedding_to_disk(cache_key, embedding)
    
    def get_embeddings_batch(self, texts: List[str]) -> Tuple[List[Optional[np.ndarray]], List[str]]:
        """
        Get cached embeddings for batch of texts
        
        Args:
            texts: List of texts to look up
            
        Returns:
            Tuple of (cached_embeddings, missing_texts)
            cached_embeddings: List of embeddings (None for missing)
            missing_texts: List of texts that weren't in cache
        """
        cached = []
        missing_indices = []
        
        for i, text in enumerate(texts):
            embedding = self.get_embedding(text)
            cached.append(embedding)
            if embedding is None:
                missing_indices.append(i)
        
        missing_texts = [texts[i] for i in missing_indices]
        return cached, missing_texts
    
    def set_embeddings_batch(self, texts: List[str], embeddings: List[np.ndarray]) -> None:
        """
        Cache embeddings for batch of texts
        
        Args:
            texts: List of texts
            embeddings: List of embeddings (can be list of lists or numpy array)
        """
        # Convert numpy array to list if needed
        if isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tolist()
        
        for text, embedding in zip(texts, embeddings):
            # Convert back to numpy array for storage
            if isinstance(embedding, list):
                embedding = np.array(embedding)
            self.set_embedding(text, embedding)
    
    # Analysis Result Cache
    def get_analysis_result(
        self, 
        criteria: str, 
        firm_names: Tuple[str, ...],
        top_n: int
    ) -> Optional[List[Dict]]:
        """
        Get cached analysis result
        
        Args:
            criteria: Investment criteria
            firm_names: Tuple of firm names (sorted for consistency)
            top_n: Number of results requested
            
        Returns:
            Cached results or None if not found/expired
        """
        cache_key = self._get_cache_key("analysis", criteria, sorted(firm_names), top_n)
        
        if cache_key in self._result_cache:
            results, timestamp = self._result_cache[cache_key]
            
            if not self._is_expired(timestamp):
                self.stats['result_hits'] += 1
                return results
            else:
                del self._result_cache[cache_key]
        
        self.stats['result_misses'] += 1
        return None
    
    def set_analysis_result(
        self,
        criteria: str,
        firm_names: Tuple[str, ...],
        top_n: int,
        results: List[Dict]
    ) -> None:
        """Cache analysis result"""
        cache_key = self._get_cache_key("analysis", criteria, sorted(firm_names), top_n)
        self._result_cache[cache_key] = (results, datetime.now())
        
        if self.enable_file_persistence:
            self._save_result_to_disk(cache_key, results)
    
    # Vector Search Cache
    def get_vector_search_result(
        self,
        query: str,
        firm_names: Tuple[str, ...],
        top_k: int
    ) -> Optional[List]:
        """Get cached vector search result"""
        cache_key = self._get_cache_key("vector_search", query, sorted(firm_names), top_k)
        
        if cache_key in self._vector_search_cache:
            results, timestamp = self._vector_search_cache[cache_key]
            
            if not self._is_expired(timestamp):
                self.stats['vector_search_hits'] += 1
                return results
            else:
                del self._vector_search_cache[cache_key]
        
        self.stats['vector_search_misses'] += 1
        return None
    
    def set_vector_search_result(
        self,
        query: str,
        firm_names: Tuple[str, ...],
        top_k: int,
        results: List
    ) -> None:
        """Cache vector search result"""
        cache_key = self._get_cache_key("vector_search", query, sorted(firm_names), top_k)
        self._vector_search_cache[cache_key] = (results, datetime.now())
    
    # File Persistence
    def _save_embedding_to_disk(self, cache_key: str, embedding: np.ndarray) -> None:
        """Save embedding to disk"""
        try:
            file_path = os.path.join(self.cache_dir, f"embedding_{cache_key}.pkl")
            with open(file_path, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            self.logger.warning(f"Failed to save embedding to disk: {e}")
    
    def _save_result_to_disk(self, cache_key: str, results: List[Dict]) -> None:
        """Save analysis result to disk"""
        try:
            file_path = os.path.join(self.cache_dir, f"result_{cache_key}.json")
            with open(file_path, 'w') as f:
                json.dump(results, f, default=str)
        except Exception as e:
            self.logger.warning(f"Failed to save result to disk: {e}")
    
    def _load_from_disk(self) -> None:
        """Load cache from disk on startup"""
        if not os.path.exists(self.cache_dir):
            return
        
        try:
            # Load embeddings (simplified - could load all if needed)
            # For now, we'll just use in-memory cache and persist new items
            self.logger.info(f"Cache directory exists: {self.cache_dir}")
        except Exception as e:
            self.logger.warning(f"Failed to load cache from disk: {e}")
    
    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """
        Clear cache
        
        Args:
            cache_type: 'embedding', 'result', 'vector_search', or None for all
        """
        if cache_type is None or cache_type == 'embedding':
            self._embedding_cache.clear()
        if cache_type is None or cache_type == 'result':
            self._result_cache.clear()
        if cache_type is None or cache_type == 'vector_search':
            self._vector_search_cache.clear()
        
        self.logger.info(f"Cache cleared: {cache_type or 'all'}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_embedding = self.stats['embedding_hits'] + self.stats['embedding_misses']
        total_result = self.stats['result_hits'] + self.stats['result_misses']
        total_vector = self.stats['vector_search_hits'] + self.stats['vector_search_misses']
        
        return {
            'embedding': {
                'hits': self.stats['embedding_hits'],
                'misses': self.stats['embedding_misses'],
                'hit_rate': self.stats['embedding_hits'] / total_embedding if total_embedding > 0 else 0,
                'total': total_embedding
            },
            'result': {
                'hits': self.stats['result_hits'],
                'misses': self.stats['result_misses'],
                'hit_rate': self.stats['result_hits'] / total_result if total_result > 0 else 0,
                'total': total_result
            },
            'vector_search': {
                'hits': self.stats['vector_search_hits'],
                'misses': self.stats['vector_search_misses'],
                'hit_rate': self.stats['vector_search_hits'] / total_vector if total_vector > 0 else 0,
                'total': total_vector
            },
            'cache_sizes': {
                'embeddings': len(self._embedding_cache),
                'results': len(self._result_cache),
                'vector_search': len(self._vector_search_cache)
            }
        }
