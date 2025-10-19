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
        Analyze firms using VC expertise
        
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
            # Build expert analysis prompt
            prompt = self._build_expert_prompt(firms, criteria)
            
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
                    max_tokens=3000,
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
                    max_tokens=3000,
                    temperature=0.4
                )
                result_text = response.choices[0].message.content
            
            # Parse and structure the response
            return self._parse_expert_analysis(result_text, top_n)
            
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
        """Build analysis prompt with firm data and investment criteria"""
        
        # Format firm data clearly
        firms_text = ""
        for i, firm in enumerate(firms, 1):
            firms_text += f"\n{'='*60}\nFIRM #{i}: {firm.get('name', 'Unknown')}\n{'='*60}\n"
            firms_text += f"Industry/Sector: {firm.get('industry', 'N/A')}\n"
            firms_text += f"Description: {firm.get('description', 'N/A')}\n"
            firms_text += f"Funding Stage: {firm.get('stage', 'N/A')}\n"
            firms_text += f"Revenue: {firm.get('revenue', 'N/A')}\n"
            firms_text += f"Location: {firm.get('location', 'N/A')}\n"
        
        return f"""Analyze these companies against the following investment criteria and rank them by fit.

INVESTMENT CRITERIA:
{criteria}

COMPANIES TO ANALYZE:
{firms_text}

INSTRUCTIONS:
For each company, provide:

1. **Match Score (0-100)**: Rate how well it fits the investment criteria
   - 90-100: Exceptional fit, all criteria met with strong fundamentals
   - 75-89: Strong fit, most criteria met
   - 60-74: Good fit, several criteria met
   - 45-59: Moderate fit, some criteria met
   - <45: Weak fit, few criteria met

2. **Investment Rationale**: 2-3 sentences explaining:
   - WHY this company matches (or doesn't match) the criteria
   - Key strengths relevant to the investment thesis
   - Specific metrics, stage appropriateness, or competitive advantages
   - Any concerns or gaps in the profile

Write as if presenting to an Investment Committee. Be specific, reference actual data points, and explain your reasoning.

Return ONLY a JSON array with this exact format:
[
  {{
    "name": "Company Name",
    "score": 85,
    "reason": "Strong B2B AI play with $10M ARR (2x the $5M threshold), positioned at Series B with $280M valuation (mid-range of target $200-400M). Enterprise focus with ML infrastructure for data analytics shows clear product-market fit. Backed by Sequoia and Accel (top-tier VCs as required). Revenue growth and stage alignment make this a compelling match for the portfolio thesis."
  }}
]

Focus on investment merit, not just keyword matching. Explain like a VC analyst."""
    
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

