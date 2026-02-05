"""
Memo Field Validator - Ensures all memo fields are populated with no empty values
Shortest implementation to prevent "information can't be found" responses
"""
import logging
from typing import Dict, Any, Optional, List

class MemoFieldValidator:
    """Validates and fills empty memo fields with reasonable defaults"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_and_fill_memo(self, memo_data: Dict[str, Any], company_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Validate memo and fill any empty fields with reasonable defaults
        
        Args:
            memo_data: Generated memo data (from LLM)
            company_data: Original company data (for fallbacks)
            
        Returns:
            Validated memo with all fields populated
        """
        # Define required fields and their defaults
        required_fields = {
            'executive_summary': 'Company overview and investment opportunity',
            'market_opportunity': 'Market size and growth potential',
            'product_technology': 'Product description and technology stack',
            'business_model': 'Revenue model and go-to-market strategy',
            'financial_analysis': 'Financial metrics and projections',
            'investment_thesis': 'Key investment rationale',
            'key_strengths': 'Primary competitive advantages',
            'key_risks': 'Main risk factors to consider',
            'recommendation': 'Investment recommendation with rationale',
            'market_size': 'Total addressable market',
            'market_growth': 'Market growth trends',
            'competitive_landscape': 'Competitive positioning',
            'revenue_model': 'How the company generates revenue',
            'unit_economics': 'Unit economics and profitability',
            'gtm_strategy': 'Go-to-market approach',
            'historical_performance': 'Past financial performance',
            'financial_projections': 'Future financial outlook',
            'key_metrics': 'Key performance indicators',
            'founder_profile': 'Founder background and experience',
            'company_background': 'Company history and business overview'
        }
        
        validated_memo = memo_data.copy()
        
        # Fill empty fields
        for field, default_template in required_fields.items():
            value = validated_memo.get(field, '').strip()
            
            # Check for "can't find" or empty responses
            if not value or self._is_empty_response(value):
                # Try to infer from company data
                inferred_value = self._infer_field(field, company_data, default_template)
                validated_memo[field] = inferred_value
                self.logger.info(f"Filled empty field '{field}' with inferred/default value")
        
        return validated_memo
    
    def _is_empty_response(self, value: str) -> bool:
        """Check if response indicates missing information"""
        empty_indicators = [
            'cannot find',
            "can't find",
            'not available',
            'n/a',
            'na',
            'none',
            'unknown',
            'not provided',
            'not found',
            'information unavailable',
            'data not available',
            'no information',
            'tbd',
            'to be determined',
            'not available in',
            'information is not available',
            'is not available in',
            'please configure openai',  # Common fallback message
            'not available in search results',
            'not available in basic mode'
        ]
        
        value_lower = value.lower().strip()
        
        # Check if value is just an empty indicator
        if not value_lower or value_lower in empty_indicators:
            return True
        
        # Check if value contains empty indicators
        # For longer messages, check if they're primarily about unavailability
        for indicator in empty_indicators:
            if indicator in value_lower:
                # If it's a short message (< 50 chars), definitely empty
                if len(value_lower) < 50:
                    return True
                # If it's longer but clearly about unavailability (contains multiple indicators or key phrases)
                if len(value_lower) < 200 and (
                    'not available' in value_lower or 
                    'cannot find' in value_lower or
                    'please configure' in value_lower
                ):
                    # Check if it's mostly about unavailability vs actual content
                    # If more than 30% of the message is about unavailability, consider it empty
                    availability_phrases = ['not available', 'cannot find', "can't find", 'please configure', 'n/a', 'unknown']
                    availability_count = sum(1 for phrase in availability_phrases if phrase in value_lower)
                    if availability_count >= 2:  # Multiple indicators = likely empty
                        return True
        
        return False
    
    def _infer_field(self, field: str, company_data: Optional[Dict], default_template: str) -> str:
        """Infer field value from company data or provide intelligent default"""
        
        if not company_data:
            return f"Based on available information: {default_template}. Further analysis recommended."
        
        # Field-specific inference logic
        inferences = {
            'executive_summary': self._infer_executive_summary(company_data),
            'market_opportunity': self._infer_market_opportunity(company_data),
            'product_technology': self._infer_product_technology(company_data),
            'business_model': self._infer_business_model(company_data),
            'financial_analysis': self._infer_financial_analysis(company_data),
            'investment_thesis': self._infer_investment_thesis(company_data),
            'key_strengths': self._infer_key_strengths(company_data),
            'key_risks': self._infer_key_risks(company_data),
            'recommendation': self._infer_recommendation(company_data),
            'market_size': self._infer_market_size(company_data),
            'market_growth': self._infer_market_growth(company_data),
            'competitive_landscape': self._infer_competitive_landscape(company_data),
            'revenue_model': self._infer_revenue_model(company_data),
            'unit_economics': self._infer_unit_economics(company_data),
            'gtm_strategy': self._infer_gtm_strategy(company_data),
            'historical_performance': self._infer_historical_performance(company_data),
            'financial_projections': self._infer_financial_projections(company_data),
            'key_metrics': self._infer_key_metrics(company_data),
            'founder_profile': self._infer_founder_profile(company_data),
            'company_background': self._infer_company_background(company_data)
        }
        
        return inferences.get(field, f"Based on available information: {default_template}. Further analysis recommended.")
    
    def _infer_executive_summary(self, company_data: Dict) -> str:
        """Infer executive summary from company data"""
        name = company_data.get('name', 'The company')
        industry = company_data.get('industry', company_data.get('Primary Industry Sector', 'technology'))
        stage = company_data.get('stage', company_data.get('Business Status', 'growth stage'))
        revenue = company_data.get('revenue', company_data.get('Revenue', 'N/A'))
        
        return f"{name} is a {industry} company at {stage} stage with reported revenue of {revenue}. The company presents an investment opportunity in the {industry} sector, with potential for growth and market expansion."
    
    def _infer_market_opportunity(self, company_data: Dict) -> str:
        """Infer market opportunity"""
        industry = company_data.get('industry', company_data.get('Primary Industry Sector', 'technology'))
        return f"The {industry} market represents a significant and growing opportunity. Market trends indicate strong demand and expansion potential in this sector. Further market research is recommended to quantify TAM, SAM, and SOM."
    
    def _infer_product_technology(self, company_data: Dict) -> str:
        """Infer product and technology"""
        name = company_data.get('name', 'The company')
        description = company_data.get('description', '')
        if description:
            return f"{name} offers: {description[:200]}. Technology stack and product details should be validated through due diligence."
        return f"{name} operates in the technology sector. Product specifications and technology stack require further investigation through company materials and technical due diligence."
    
    def _infer_business_model(self, company_data: Dict) -> str:
        """Infer business model"""
        industry = company_data.get('industry', 'technology')
        return f"Business model appears to be {industry}-focused. Revenue model, pricing strategy, and go-to-market approach should be confirmed through company discussions and financial analysis."
    
    def _infer_financial_analysis(self, company_data: Dict) -> str:
        """Infer financial analysis"""
        revenue = company_data.get('revenue', company_data.get('Revenue', 'Not disclosed'))
        growth = company_data.get('growth_rate', company_data.get('Growth Rate', 'Not disclosed'))
        return f"Financial metrics indicate revenue of {revenue} with growth rate of {growth}. Detailed financial analysis including P&L, balance sheet, and cash flow statements should be obtained for comprehensive evaluation."
    
    def _infer_investment_thesis(self, company_data: Dict) -> str:
        """Infer investment thesis"""
        name = company_data.get('name', 'The company')
        industry = company_data.get('industry', 'technology')
        return f"Investment thesis centers on {name}'s position in the {industry} sector, with potential for market leadership, strong unit economics, and scalable growth. Key value drivers should be validated through deeper analysis."
    
    def _infer_key_strengths(self, company_data: Dict) -> str:
        """Infer key strengths"""
        investors = company_data.get('Active Investors', company_data.get('active_investors', ''))
        if investors:
            return f"Key strengths include backing from {investors}, indicating strong investor validation. Additional strengths such as market position, technology, and team should be assessed through due diligence."
        return "Key strengths include market positioning and growth potential. Specific competitive advantages, technology moats, and team capabilities should be evaluated through comprehensive due diligence."
    
    def _infer_key_risks(self, company_data: Dict) -> str:
        """Infer key risks"""
        stage = company_data.get('stage', company_data.get('Business Status', 'growth stage'))
        return f"Key risks typical for {stage} companies include market competition, execution risk, regulatory considerations, and scaling challenges. Risk assessment should be completed through detailed due diligence."
    
    def _infer_recommendation(self, company_data: Dict) -> str:
        """Infer recommendation"""
        return "Recommendation pending comprehensive analysis. Further due diligence required to assess investment fit, valuation, terms, and strategic alignment with investment criteria."
    
    def _infer_market_size(self, company_data: Dict) -> str:
        """Infer market size"""
        industry = company_data.get('industry', 'technology')
        return f"Total addressable market (TAM) for {industry} sector is substantial. Market sizing analysis should be conducted to quantify TAM, serviceable addressable market (SAM), and serviceable obtainable market (SOM)."
    
    def _infer_market_growth(self, company_data: Dict) -> str:
        """Infer market growth"""
        return "Market growth trends indicate positive trajectory. Industry growth rates and market expansion trends should be analyzed through market research and industry reports."
    
    def _infer_competitive_landscape(self, company_data: Dict) -> str:
        """Infer competitive landscape"""
        industry = company_data.get('industry', 'technology')
        return f"Competitive landscape in {industry} includes established players and emerging competitors. Competitive analysis should identify key competitors, market share, and differentiation strategies."
    
    def _infer_revenue_model(self, company_data: Dict) -> str:
        """Infer revenue model"""
        return "Revenue model should be confirmed through company discussions. Typical models include subscription, transaction-based, or enterprise licensing. Revenue streams and pricing should be validated."
    
    def _infer_unit_economics(self, company_data: Dict) -> str:
        """Infer unit economics"""
        return "Unit economics including CAC, LTV, payback period, and gross margins should be analyzed through financial data and operational metrics. Company should provide unit economics analysis."
    
    def _infer_gtm_strategy(self, company_data: Dict) -> str:
        """Infer go-to-market strategy"""
        return "Go-to-market strategy including sales channels, customer acquisition approach, and marketing strategy should be discussed with company leadership and validated through customer interviews."
    
    def _infer_historical_performance(self, company_data: Dict) -> str:
        """Infer historical performance"""
        revenue = company_data.get('revenue', company_data.get('Revenue', 'Not disclosed'))
        growth = company_data.get('growth_rate', company_data.get('Growth Rate', 'Not disclosed'))
        return f"Historical performance shows revenue of {revenue} with growth of {growth}. Detailed historical financials including revenue trends, customer growth, and key milestones should be obtained."
    
    def _infer_financial_projections(self, company_data: Dict) -> str:
        """Infer financial projections"""
        return "Financial projections including revenue forecasts, growth assumptions, and key financial metrics should be obtained from company financial models and validated through sensitivity analysis."
    
    def _infer_key_metrics(self, company_data: Dict) -> str:
        """Infer key metrics"""
        revenue = company_data.get('revenue', company_data.get('Revenue', 'Not disclosed'))
        growth = company_data.get('growth_rate', company_data.get('Growth Rate', 'Not disclosed'))
        employees = company_data.get('employees', company_data.get('Employees', 'Not disclosed'))
        return f"Key metrics include revenue ({revenue}), growth rate ({growth}), and team size ({employees}). Additional KPIs should be identified based on business model and industry benchmarks."
    
    def _infer_founder_profile(self, company_data: Dict) -> str:
        """Infer founder profile"""
        name = company_data.get('name', 'The company')
        industry = company_data.get('industry', company_data.get('Primary Industry Sector', 'technology'))
        stage = company_data.get('stage', company_data.get('Business Status', 'growth stage'))
        
        return f"""**Founder Analysis (Based on Industry Patterns):**

Founder information for {name} should be obtained through:
- Company website (About/Team page)
- LinkedIn profiles of founders and executives
- PitchBook founder data and previous companies
- Crunchbase founder profiles
- Industry publications and interviews

**Typical Founder Profile for {industry} Companies at {stage} Stage:**

Founders in the {industry} sector typically have backgrounds in:
- **Technical Expertise**: Deep knowledge in {industry} technology, software development, or engineering
- **Industry Experience**: Previous roles at established {industry} companies or related tech firms
- **Entrepreneurial Track Record**: Prior startup experience, successful exits, or serial entrepreneurship
- **Domain Knowledge**: Understanding of {industry} market dynamics, customer needs, and industry trends
- **Leadership Experience**: Experience building and scaling teams, products, and businesses

**Key Areas to Investigate:**
1. **Educational Background**: Technical degrees (CS, Engineering) or business degrees (MBA) relevant to {industry}
2. **Previous Companies**: Track record at successful {industry} companies or startups
3. **Years of Experience**: Typically 10-20+ years in {industry} or related technology sectors
4. **Notable Achievements**: Previous exits, patents, publications, or industry recognition
5. **Network**: Connections to investors, advisors, and industry leaders in {industry}

**Due Diligence Recommendations:**
- Review founder LinkedIn profiles for detailed background
- Check PitchBook for founder's previous companies and exits
- Conduct reference checks with previous colleagues or investors
- Assess founder-market fit and domain expertise
- Evaluate founder's ability to execute and scale the business

**Note**: Specific founder names, educational details, and previous company information should be obtained through direct company materials, founder interviews, and professional networking platforms."""
    
    def _infer_company_background(self, company_data: Dict) -> str:
        """Infer company background"""
        name = company_data.get('name', 'The company')
        industry = company_data.get('industry', company_data.get('Primary Industry Sector', 'technology'))
        description = company_data.get('description', '')
        revenue = company_data.get('revenue', company_data.get('Revenue', 'Not disclosed'))
        stage = company_data.get('stage', company_data.get('Business Status', 'growth stage'))
        
        if description:
            background = f"{name} is a {industry} company. {description[:300]}"
        else:
            background = f"{name} operates in the {industry} sector, focusing on innovative solutions and market opportunities in this space."
        
        return f"""{background}

**Company Overview:**
- **Industry**: {industry}
- **Stage**: {stage}
- **Revenue**: {revenue}

**Business Model & Operations:**
The company's business model and operational structure should be confirmed through company discussions and materials. Typical for {industry} companies at {stage} stage, the business likely focuses on:
- Product development and market validation
- Customer acquisition and growth
- Revenue generation and unit economics optimization
- Team building and organizational development

**Key Milestones & History:**
Company history, founding story, and key milestones should be obtained through:
- Company website and About page
- Press releases and media coverage
- PitchBook company profile
- Industry databases and research reports

**Financial Context:**
Based on available information, {industry} companies at {stage} stage typically have:
- Revenue ranging from $1M-$50M (depending on business model and market)
- Team size of 10-200 employees
- Funding history appropriate for the stage
- Growth trajectory aligned with market opportunity

**Due Diligence Recommendations:**
- Review company website, investor materials, and pitch decks
- Analyze financial statements and key metrics
- Conduct customer and partner interviews
- Assess market position and competitive landscape
- Evaluate technology, product, and team capabilities"""


def enhance_prompt_for_complete_fields(base_prompt: str) -> str:
    """
    Enhance prompt to ensure all fields are populated
    
    Args:
        base_prompt: Original prompt
        
    Returns:
        Enhanced prompt with field completion instructions
    """
    field_completion_instructions = """

CRITICAL FIELD COMPLETION REQUIREMENTS:
- NEVER respond with "information can't be found", "not available", "N/A", or similar empty responses
- ALWAYS provide a meaningful analysis, inference, or professional assessment for every field
- If specific data is missing, make reasonable inferences based on:
  * Company name and industry
  * Available company data fields
  * Industry benchmarks and typical patterns
  * Professional VC analyst judgment
- Use phrases like "Based on available information...", "Typical for this stage...", "Industry analysis suggests..."
- Every field MUST contain substantive content (minimum 2-3 sentences)
- If exact data is unavailable, provide analysis framework or assessment approach

REQUIRED FIELDS - ALL MUST BE POPULATED:
1. Executive Summary: Company overview and investment opportunity (always provide)
2. Market Opportunity: Market size and growth (infer from industry if needed)
3. Product & Technology: Product description (infer from company description if needed)
4. Business Model: Revenue model (infer from industry patterns if needed)
5. Financial Analysis: Financial metrics (use available data, note what's missing)
6. Investment Thesis: Investment rationale (always provide based on available info)
7. Key Strengths: Competitive advantages (infer from investors, stage, industry)
8. Key Risks: Risk factors (provide typical risks for stage/industry)
9. Recommendation: Investment recommendation (always provide with rationale)

REMEMBER: It's better to provide an informed inference or analysis framework than to say "can't find".
A professional VC analyst always provides value, even when some data points are missing.
"""
    
    return base_prompt + field_completion_instructions
