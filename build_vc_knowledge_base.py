"""
Script to build VC Knowledge Base
Run this to collect VC industry knowledge and train the knowledge base
"""
import logging
from vc_data_search_agent import VCDataSearchAgent
from vc_knowledge_training_agent import VCKnowledgeTrainingAgent
from config import Config
from embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_vc_knowledge_base(max_items: int = 100):
    """
    Build VC knowledge base by collecting and training on VC data
    
    Args:
        max_items: Maximum knowledge items to collect
    """
    logger.info("=" * 60)
    logger.info("Building VC Knowledge Base")
    logger.info("=" * 60)
    
    # Step 1: Search for VC knowledge
    logger.info("\n📡 Step 1: Searching for VC industry knowledge...")
    search_agent = VCDataSearchAgent()
    knowledge_items = search_agent.collect_vc_knowledge_base(max_items=max_items)
    
    logger.info(f"✅ Collected {len(knowledge_items)} VC knowledge items")
    
    if len(knowledge_items) == 0:
        logger.warning("⚠️ No knowledge items collected. Check internet connection and DuckDuckGo availability.")
        return
    
    # Step 2: Train knowledge base
    logger.info("\n🧠 Step 2: Training VC Knowledge Base...")
    config = Config()
    
    # Initialize embedding service
    embedding_service = EmbeddingService(config, use_openai=False)  # Use local embeddings (free)
    
    # Initialize training agent
    training_agent = VCKnowledgeTrainingAgent(config, embedding_service=embedding_service)
    
    # Train on collected knowledge
    stats = training_agent.train_on_vc_data(knowledge_items)
    
    logger.info("\n" + "=" * 60)
    logger.info("Training Complete!")
    logger.info("=" * 60)
    logger.info(f"Total items processed: {stats['processed']}")
    logger.info(f"Total chunks created: {stats['total_chunks']}")
    logger.info(f"Errors: {stats['errors']}")
    
    logger.info("\n✅ VC Knowledge Base is ready to use!")
    logger.info("You can now use it in research with EnhancedVCResearchAgent")
    
    return training_agent


if __name__ == "__main__":
    # Build knowledge base with 100 items
    training_agent = build_vc_knowledge_base(max_items=100)
    
    # Test retrieval
    if training_agent:
        logger.info("\n🧪 Testing knowledge base retrieval...")
        context = training_agent.get_vc_context("venture capital valuation methods", top_k=3)
        if context:
            logger.info("✅ Knowledge base retrieval working!")
            logger.info(f"Retrieved context ({len(context)} chars)")
        else:
            logger.warning("⚠️ No context retrieved. Knowledge base may be empty.")
