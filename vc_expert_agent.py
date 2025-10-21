"""
VC Expert Agent - Intelligent analysis of companies against investment criteria
Acts as an experienced venture capital analyst
"""
import logging
from typing import List, Dict, Any

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    OPENAI_VERSION = int(openai.__version__.split('.')[0])
except ImportError:
    OPENAI_AVAILABLE = False
    OPENAI_VERSION = 0
    logging.warning("OpenAI module not available. Install with: pip install openai")


class VCExpertAgent:
    """AI agent with VC expertise for analyzing investment opportunities"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._setup_openai()
    
    def _setup_openai(self):
        """Initialize OpenAI client"""
        if OPENAI_AVAILABLE:
            api_key = self.config.get_openai_key()
            if api_key:
                if OPENAI_VERSION >= 1:
                    # New API (OpenAI 1.0+)
                    self.client = OpenAI(api_key=api_key)
                else:
                    # Old API (OpenAI 0.x)
                    openai.api_key = api_key
        else:
            self.logger.warning("OpenAI not available - install with: pip install openai")
    
    def analyze_firms(self, firms: List[Dict], criteria: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Analyze firms using VC expertise with batching to avoid token limits
        
        Args:
            firms: List of firm data dictionaries
            criteria: Investment criteria/heuristics
            top_n: Number of top matches to return
            
        Returns:
            List of analyzed firms with expert reasoning
        """
        # Check if OpenAI is available
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI module not installed. Install with: pip install openai")
        
        # Check if API key is configured
        if not self.config.get_openai_key():
            raise ValueError("OpenAI API key not configured")
        
        try:
            # Process in smaller batches to avoid token limits
            batch_size = 5  # Process 5 companies at a time (very safe for token limits)
            all_results = []
            
            for i in range(0, len(firms), batch_size):
                batch = firms[i:i + batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1}/{(len(firms)-1)//batch_size + 1} ({len(batch)} companies)")
                
                # Build expert analysis prompt for this batch
                prompt = self._build_expert_prompt(batch, criteria)
                
                # Get analysis from AI with VC context
                if OPENAI_VERSION >= 1:
                    # New API (OpenAI 1.0+)
                    response = self.client.chat.completions.create(
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
                else:
                    # Old API (OpenAI 0.x)
                    response = openai.ChatCompletion.create(
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
                
                # Parse this batch's results
                batch_results = self._parse_expert_analysis(result_text, len(batch))
                all_results.extend(batch_results)
            
            # Sort all results by score and return top N
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            return all_results[:top_n]
            
        except Exception as e:
            self.logger.error(f"VC Expert Agent error: {str(e)}")
            raise
    
    def _get_vc_expert_system_prompt(self) -> str:
        """System prompt defining the VC expert persona"""
        return """You are a seasoned venture capital analyst with 15+ years of experience in tech investments, specializing in AI/ML, B2B SaaS, and growth-stage companies.

Your expertise includes:
- Evaluating company-market fit and investment potential
- Understanding funding stages, valuations, and metrics (ARR, growth rates, burn)
- Assessing business models (B2B vs B2C, enterprise vs SMB)
- Analyzing competitive positioning and moat
- Evaluating investor quality and syndicate strength
- Understanding sector dynamics (AI/ML, SaaS, fintech, etc.)

Your analysis style:
- Professional, concise, and data-driven
- References specific metrics and benchmarks
- Explains WHY companies match investment criteria
- Provides context on valuations, stages, and market positioning
- Identifies strengths, risks, and strategic fit
- Scores based on overall investment thesis alignment

You analyze companies against specific investment criteria and explain matches like you would in a partner meeting or IC (Investment Committee) memo."""
    
    def _build_expert_prompt(self, firms: List[Dict], criteria: str) -> str:
        """Build analysis prompt with ALL firm data and investment criteria"""
        
        # Format firm data with ALL available fields
        firms_text = ""
        for i, firm in enumerate(firms, 1):
            firms_text += f"\n{'='*60}\nFIRM #{i}: {firm.get('name', 'Unknown')}\n{'='*60}\n"
            
            # Key fields first
            priority_fields = ['name', 'description', 'industry', 'stage', 'revenue', 'location']
            
            for field in priority_fields:
                if field in firm:
                    label = field.replace('_', ' ').title()
                    firms_text += f"{label}: {firm[field]}\n"
            
            # Then key investment fields only (to reduce token usage)
            key_investment_fields = [
                'Revenue', 'Growth Rate', 'Total Raised', 'Active Investors', 
                'First Financing Valuation', 'Success Probability', 'Employees',
                'Year Founded', 'Business Status', 'Primary Industry Sector'
            ]
            
            for field in key_investment_fields:
                if field in firm and firm[field] and str(firm[field]).strip() != '':
                    value = str(firm[field])
                    if len(value) > 50:  # Truncate long values
                        value = value[:50] + "..."
                    firms_text += f"  • {field}: {value}\n"
        
        return f"""Analyze these companies against the following investment criteria and rank them by fit.

INVESTMENT CRITERIA:
{criteria}

COMPANIES TO ANALYZE:
{firms_text}

INSTRUCTIONS:
You are a senior VC analyst with access to comprehensive PitchBook data. Analyze each company using ALL available data fields including:

🎯 **Key Investment Metrics to Focus On:**
- Revenue & Growth: Revenue, Growth Rate, Growth Rate Percentile, Web Growth Rate
- Valuation & Financing: First Financing Valuation, Total Raised, Last Financing Size
- Investor Quality: Active Investors, Former Investors, Success Probability
- Company Stage: Business Status, Year Founded, Employees, IPO/M&A Probability
- Market Position: Primary Industry Sector, Verticals, Keywords, Emerging Spaces

For each company, provide:

1. **Match Score (0-100)**: Rate how well it fits the investment criteria
   - 90-100: Exceptional fit, all criteria met with strong fundamentals
   - 75-89: Strong fit, most criteria met
   - 60-74: Good fit, several criteria met
   - 45-59: Moderate fit, some criteria met
   - <45: Weak fit, few criteria met

2. **Investment Rationale**: 2-3 sentences explaining:
   - WHY this company matches (or doesn't match) the criteria
   - SPECIFIC data points: revenue amounts, growth rates, valuation ranges, investor names, success probabilities
   - Stage appropriateness, competitive positioning, and market validation
   - Key strengths or concerns based on ALL available PitchBook data

Write as if presenting to an Investment Committee. Use SPECIFIC data points from all available fields.

Return ONLY a JSON array with this exact format:
[{{"name": "Company Name", "score": 87, "reason": "Strong B2B AI opportunity with $10M ARR (2x threshold) and 45% growth rate. $280M valuation (within target). Backed by Sequoia, a16z (tier-1 VCs). Series B with 82% success probability. 150 employees (3x YoY). Web traffic growth (75th percentile)."}}]

Focus on investment merit using ALL available PitchBook data. Be specific and data-driven like a VC analyst."""
    
    def _parse_expert_analysis(self, response_text: str, top_n: int) -> List[Dict]:
        """Parse expert analysis response into structured results"""
        try:
            import json
            
            # Extract JSON from response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                results = json.loads(json_text)
                
                # Sort by score and return top N
                results_sorted = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
                
                return [
                    {
                        'name': firm.get('name', 'Unknown'),
                        'score': float(firm.get('score', 0)),
                        'reason': firm.get('reason', 'No analysis provided')
                    }
                    for firm in results_sorted[:top_n]
                ]
            else:
                raise ValueError("No valid JSON found in expert analysis")
                
        except Exception as e:
            self.logger.error(f"Error parsing expert analysis: {str(e)}")
            self.logger.debug(f"Raw response: {response_text}")
            raise
    
    def is_available(self) -> bool:
        """Check if VC expert agent can be used (requires API key and OpenAI module)"""
        return OPENAI_AVAILABLE and bool(self.config.get_openai_key())

