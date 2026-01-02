"""
Hybrid Filter: Combines Vector Search (fast pre-filtering) + LLM Analysis (detailed reasoning)
This provides both speed and accuracy
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from embedding_service import EmbeddingService
from vector_store import VectorStore
from vc_expert_agent import VCExpertAgent
from vc_expert_agent_async import VCExpertAgentAsync
from config import Config
from cache_service import CacheService
from document_store import DocumentStore


class HybridFilter:
    """
    Hybrid filtering approach:
    1. Vector search (fast semantic pre-filtering) → top 50-100 candidates
    2. LLM analysis (detailed reasoning) → top 10 final results
    """
    
    def __init__(
        self, 
        config: Config, 
        use_openai_embeddings: bool = False,
        cache_service: Optional[CacheService] = None
    ):
        """
        Initialize hybrid filter
        
        Args:
            config: Configuration object
            use_openai_embeddings: If True, use OpenAI embeddings (cloud).
                                  If False, use sentence-transformers (local, free)
            cache_service: Optional cache service for caching embeddings and results
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.cache_service = cache_service
        
        # Initialize embedding service with cache
        try:
            self.embedding_service = EmbeddingService(
                config, 
                use_openai=use_openai_embeddings,
                cache_service=cache_service
            )
        except ImportError as e:
            self.logger.warning(f"Embedding service not available: {e}")
            self.embedding_service = None
        
        # Initialize vector store
        self.vector_store = VectorStore(self.embedding_service) if self.embedding_service else None
        
        # Initialize document store for RAG (if provided)
        self.document_store = None
        
        # Initialize VC Expert Agent for detailed analysis (with optional RAG)
        self.vc_expert = VCExpertAgent(config, document_store=self.document_store)
        
        # Try to initialize async version (faster)
        try:
            self.vc_expert_async = VCExpertAgentAsync(config)
            self.vc_expert_async.document_store = self.document_store  # Share document store
            self.use_async = self.vc_expert_async.async_client is not None
        except Exception as e:
            self.logger.warning(f"Async VC Expert not available: {e}")
            self.vc_expert_async = None
            self.use_async = False
    
    def set_document_store(self, document_store: DocumentStore) -> None:
        """
        Set document store for RAG (call after initialization)
        
        Args:
            document_store: DocumentStore instance with ingested documents
        """
        self.document_store = document_store
        self.vc_expert.document_store = document_store
        if self.vc_expert_async:
            self.vc_expert_async.document_store = document_store
        self.logger.info("Document store set for RAG")
        
        # Configuration
        self.vector_search_top_k = 50  # Pre-filter to top 50 candidates
        self.final_top_n = 10  # Final results to return
    
    def filter_firms(
        self, 
        firms: List[Dict], 
        criteria: str, 
        top_n: int = 10,
        use_vector_search: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Filter firms using hybrid approach
        
        Args:
            firms: List of firm dictionaries
            criteria: Investment criteria/heuristics
            top_n: Number of top results to return
            use_vector_search: If True, use vector search pre-filtering.
                              If False, analyze all firms (slower but more thorough)
            
        Returns:
            List of filtered firms with scores and reasons
        """
        self.final_top_n = top_n
        
        # If vector search is not available or disabled, fall back to full LLM analysis
        if not use_vector_search or not self.vector_store or not self.embedding_service:
            self.logger.info("Using full LLM analysis (vector search unavailable or disabled)")
            return self._full_llm_analysis(firms, criteria, top_n)
        
        # Step 1: Vector search for fast pre-filtering
        self.logger.info(f"Step 1: Vector search pre-filtering ({len(firms)} → top {self.vector_search_top_k})")
        
        # Check cache for vector search results
        firm_names = tuple(sorted([f.get('name', '') for f in firms]))
        cached_vector_results = None
        if self.cache_service:
            cached_vector_results = self.cache_service.get_vector_search_result(
                criteria, firm_names, self.vector_search_top_k
            )
        
        if cached_vector_results:
            self.logger.info("Cache hit for vector search results")
            vector_results = cached_vector_results
        else:
            # Add firms to vector store
            self.vector_store.clear()
            self.vector_store.add_firms(firms)
            
            # Search for top candidates
            vector_results = self.vector_store.search(criteria, top_k=self.vector_search_top_k)
            
            # Cache the results
            if self.cache_service and vector_results:
                self.cache_service.set_vector_search_result(
                    criteria, firm_names, self.vector_search_top_k, vector_results
                )
        
        if not vector_results:
            self.logger.warning("Vector search returned no results, falling back to full analysis")
            return self._full_llm_analysis(firms, criteria, top_n)
        
        # Extract candidate firms (top K from vector search)
        candidate_firms = [firm for firm, score in vector_results]
        vector_scores = {firm.get('name'): score for firm, score in vector_results}
        
        self.logger.info(f"Step 2: Detailed LLM analysis of {len(candidate_firms)} candidates")
        
        # Check cache for analysis results
        candidate_names = tuple(sorted([f.get('name', '') for f in candidate_firms]))
        cached_results = None
        if self.cache_service:
            cached_results = self.cache_service.get_analysis_result(
                criteria, candidate_names, top_n
            )
        
        if cached_results:
            self.logger.info("Cache hit for analysis results")
            # Add vector similarity scores to cached results
            for result in cached_results:
                firm_name = result.get('name', '')
                vector_score = vector_scores.get(firm_name, 0.0)
                result['vector_similarity'] = vector_score
            return cached_results
        
        # Step 2: Detailed LLM analysis on pre-filtered candidates
        try:
            # Use async version if available (much faster)
            if self.use_async and self.vc_expert_async:
                self.logger.info("Using async parallel processing for faster analysis")
                # Run async function in sync context (Streamlit compatible)
                # Streamlit doesn't run in async context, so asyncio.run() is safe
                llm_results = asyncio.run(
                    self.vc_expert_async.analyze_firms_async(
                        candidate_firms, 
                        criteria, 
                        top_n=top_n,
                        max_concurrent=5  # Process 5 batches in parallel
                    )
                )
            else:
                self.logger.info("Using sync processing (async not available)")
                llm_results = self.vc_expert.analyze_firms(candidate_firms, criteria, top_n=top_n)
            
            # Combine vector similarity score with LLM score (for transparency)
            for result in llm_results:
                firm_name = result.get('name', '')
                vector_score = vector_scores.get(firm_name, 0.0)
                result['vector_similarity'] = vector_score
            
            # Cache the results
            if self.cache_service:
                self.cache_service.set_analysis_result(
                    criteria, candidate_names, top_n, llm_results
                )
            
            return llm_results
            
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}, falling back to vector search results")
            # Fallback: return vector search results with basic formatting
            return self._format_vector_results(vector_results[:top_n])
    
    def _full_llm_analysis(
        self, 
        firms: List[Dict], 
        criteria: str, 
        top_n: int
    ) -> List[Dict[str, Any]]:
        """Fallback: Full LLM analysis of all firms (no vector pre-filtering)"""
        if not self.vc_expert.is_available():
            self.logger.error("VC Expert Agent not available for full analysis")
            return []
        
        return self.vc_expert.analyze_firms(firms, criteria, top_n=top_n)
    
    def _format_vector_results(
        self, 
        vector_results: List[tuple]
    ) -> List[Dict[str, Any]]:
        """Format vector search results into expected format"""
        formatted = []
        for firm, similarity_score in vector_results:
            formatted.append({
                'name': firm.get('name', 'Unknown'),
                'score': similarity_score * 100,  # Convert 0-1 to 0-100
                'reason': f"Semantic match (similarity: {similarity_score:.2f}). "
                         f"Matches criteria based on company description, industry, and other attributes.",
                'vector_similarity': similarity_score
            })
        return formatted
    
    def is_vector_search_available(self) -> bool:
        """Check if vector search is available"""
        return self.vector_store is not None and self.embedding_service is not None
