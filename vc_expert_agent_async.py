"""
Async VC Expert Agent - Parallel batch processing for faster analysis
"""
import asyncio
import logging
from typing import List, Dict, Any
from vc_expert_agent import VCExpertAgent, OPENAI_AVAILABLE, OPENAI_VERSION

try:
    from openai import AsyncOpenAI
    ASYNC_OPENAI_AVAILABLE = True
except ImportError:
    ASYNC_OPENAI_AVAILABLE = False


class VCExpertAgentAsync(VCExpertAgent):
    """Async version of VC Expert Agent with parallel batch processing"""
    
    def __init__(self, config, document_store=None):
        """Initialize async VC Expert Agent"""
        super().__init__(config, document_store=document_store)
        
        # Create async client
        if ASYNC_OPENAI_AVAILABLE and OPENAI_AVAILABLE:
            api_key = config.get_openai_key()
            if api_key:
                if OPENAI_VERSION >= 1:
                    self.async_client = AsyncOpenAI(api_key=api_key)
                else:
                    self.async_client = None
                    self.logger.warning("Async client requires OpenAI 1.0+, falling back to sync")
            else:
                self.async_client = None
        else:
            self.async_client = None
    
    async def analyze_firms_async(
        self, 
        firms: List[Dict], 
        criteria: str, 
        top_n: int = 10,
        batch_size: int = 5,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analyze firms using async parallel processing
        
        Args:
            firms: List of firm data dictionaries
            criteria: Investment criteria/heuristics
            top_n: Number of top matches to return
            batch_size: Number of firms per batch
            max_concurrent: Maximum number of concurrent API calls
            
        Returns:
            List of analyzed firms with expert reasoning
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI module not installed. Install with: pip install openai")
        
        if not self.config.get_openai_key():
            raise ValueError("OpenAI API key not configured")
        
        if not self.async_client:
            self.logger.warning("Async client not available, falling back to sync processing")
            return self.analyze_firms(firms, criteria, top_n)
        
        try:
            # Split firms into batches
            batches = [
                firms[i:i + batch_size] 
                for i in range(0, len(firms), batch_size)
            ]
            
            self.logger.info(
                f"Processing {len(firms)} firms in {len(batches)} batches "
                f"with max {max_concurrent} concurrent requests"
            )
            
            # Process batches with concurrency limit
            semaphore = asyncio.Semaphore(max_concurrent)
            tasks = [
                self._analyze_batch_async(batch, criteria, semaphore, batch_idx, len(batches))
                for batch_idx, batch in enumerate(batches)
            ]
            
            # Wait for all batches to complete
            batch_results = await asyncio.gather(*tasks)
            
            # Flatten results
            all_results = []
            for results in batch_results:
                all_results.extend(results)
            
            # Sort by score and return top N
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            return all_results[:top_n]
            
        except Exception as e:
            self.logger.error(f"Async VC Expert Agent error: {str(e)}")
            raise
    
    async def _analyze_batch_async(
        self, 
        batch: List[Dict], 
        criteria: str, 
        semaphore: asyncio.Semaphore,
        batch_idx: int,
        total_batches: int
    ) -> List[Dict]:
        """
        Analyze a single batch asynchronously with semaphore for concurrency control
        
        Args:
            batch: Batch of firms to analyze
            criteria: Investment criteria
            semaphore: Semaphore to limit concurrent requests
            batch_idx: Current batch index (for logging)
            total_batches: Total number of batches (for logging)
            
        Returns:
            List of analysis results for this batch
        """
        async with semaphore:
            self.logger.info(
                f"Processing batch {batch_idx + 1}/{total_batches} "
                f"({len(batch)} companies)"
            )
            
            try:
                # Build prompt
                prompt = self._build_expert_prompt(batch, criteria)
                
                # Async API call
                response = await self.async_client.chat.completions.create(
                    model=self.config.get_ai_model(),
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_vc_expert_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.4
                )
                
                result_text = response.choices[0].message.content
                
                # Parse results
                batch_results = self._parse_expert_analysis(result_text, len(batch))
                
                self.logger.info(
                    f"Batch {batch_idx + 1}/{total_batches} complete "
                    f"({len(batch_results)} results)"
                )
                
                return batch_results
                
            except Exception as e:
                self.logger.error(f"Error in batch {batch_idx + 1}: {str(e)}")
                # Return empty results for this batch
                return []
