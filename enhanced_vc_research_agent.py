"""
Enhanced VC Research Agent
Comprehensive research with VC knowledge base integration, thematic searches, and time-series analysis
"""
import logging
from typing import Dict, Optional, List
from company_research_agent import CompanyResearchAgent
from vc_knowledge_training_agent import VCKnowledgeTrainingAgent
from data_validation_agent import DataValidationAgent
from config import Config

logger = logging.getLogger(__name__)


class EnhancedVCResearchAgent:
    """Enhanced research agent with VC knowledge base and comprehensive thematic searches"""
    
    def __init__(self, config: Config, vc_knowledge_agent: Optional[VCKnowledgeTrainingAgent] = None):
        self.config = config
        self.logger = logger
        
        # Base research agent
        self.base_research_agent = CompanyResearchAgent(config)
        
        # VC knowledge agent (optional)
        self.vc_knowledge_agent = vc_knowledge_agent
        
        # Data validation agent
        self.validation_agent = DataValidationAgent()
    
    def research_company_comprehensive(
        self,
        company_name: str,
        excel_data: Dict,
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """
        Perform comprehensive research with VC knowledge integration
        
        Args:
            company_name: Name of company to research
            excel_data: Data from Excel sheet
            additional_info: Additional context
            
        Returns:
            Comprehensive research data with validation
        """
        self.logger.info(f"Starting comprehensive research for {company_name}")
        
        # Step 1: Validate Excel data
        excel_validation = self.validation_agent.validate_excel_data(excel_data, company_name)
        self.logger.info(f"Excel validation: {excel_validation['is_valid']}, Confidence: {excel_validation['confidence']:.2f}")
        
        # Step 2: Perform thematic research
        research_data = self._thematic_research(company_name, excel_data, additional_info)
        
        # Step 3: Cross-check Excel vs Research
        cross_check = self.validation_agent.cross_check_data(excel_data, research_data, company_name)
        self.logger.info(f"Cross-check: {len(cross_check['matches'])} matches, {len(cross_check['discrepancies'])} discrepancies")
        
        # Step 4: Fill missing data
        filled_data = self.validation_agent.fill_missing_data(
            excel_data,
            research_data,
            excel_data
        )
        
        # Step 5: VC knowledge base is used for training the agent (not as context)
        # The agent has learned VC best practices and applies them automatically
        # No need to inject VC context here - it's already in the agent's training
        
        # Step 6: Return enhanced research (VC knowledge is in agent's system prompt, not here)
        enhanced_research = research_data
        
        # Step 7: Add validation metadata
        enhanced_research['_validation'] = {
            'excel_validation': excel_validation,
            'cross_check': cross_check,
            'filled_data': filled_data,
            'data_sources': filled_data.get('data_sources', {}),
        }
        
        return enhanced_research
    
    def _thematic_research(
        self,
        company_name: str,
        excel_data: Dict,
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """
        Perform thematic research across multiple areas
        
        Themes:
        1. Market size & growth (with time-series)
        2. Competitive landscape (with market share)
        3. Founder background (with previous exits)
        4. Funding history (with valuation trends)
        5. Industry benchmarks (with comparables)
        6. Market pace indicators
        """
        # Use base research agent but with enhanced queries
        enhanced_info = additional_info or {}
        enhanced_info.update(excel_data)
        
        # Perform base research
        research_data = self.base_research_agent.research_company(company_name, enhanced_info)
        
        # Add thematic enhancements
        research_data['thematic_analysis'] = {
            'market_pace': self._analyze_market_pace(company_name, excel_data),
            'time_series_data': self._extract_time_series(company_name, excel_data),
            'industry_benchmarks': self._get_industry_benchmarks(excel_data),
        }
        
        return research_data
    
    def _analyze_market_pace(self, company_name: str, excel_data: Dict) -> Dict:
        """Analyze market pace indicators"""
        # This would search for funding velocity, exit timelines, etc.
        # For now, return placeholder
        return {
            'funding_velocity': 'Not available',
            'exit_timeline': 'Not available',
            'market_cycle': 'Not available',
        }
    
    def _extract_time_series(self, company_name: str, excel_data: Dict) -> Dict:
        """Extract time-series data (market growth over time)"""
        # This would extract historical market data
        return {
            'market_growth_history': 'Not available',
            'funding_trends': 'Not available',
        }
    
    def _get_industry_benchmarks(self, excel_data: Dict) -> Dict:
        """Get industry benchmarks for comparison"""
        industry = excel_data.get('industry', '')
        if not industry:
            return {}
        
        # This would use VC knowledge base to get benchmarks
        return {
            'typical_valuation_range': 'Not available',
            'typical_revenue_range': 'Not available',
            'typical_growth_rate': 'Not available',
        }
    
    # Removed _enhance_with_vc_context - VC knowledge is now used for agent training, not context injection
