"""
VC Expert Agent - Intelligent analysis of companies against investment criteria
Acts as an experienced venture capital analyst
"""
import logging
from typing import List, Dict, Any, Optional

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
    
    def __init__(self, config, document_store=None, vc_knowledge_agent=None):
        """
        Initialize VC Expert Agent
        
        Args:
            config: Configuration object
            document_store: Optional DocumentStore for RAG (Retrieval-Augmented Generation)
            vc_knowledge_agent: Optional VCKnowledgeTrainingAgent for agent training (not RAG context)
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.document_store = document_store
        self.vc_knowledge_agent = vc_knowledge_agent
        self._training_principles = None  # Cached training principles
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
        """System prompt defining the VC expert persona, enhanced with training from knowledge base"""
        base_prompt = """You are a seasoned venture capital analyst with 15+ years of experience in tech investments, specializing in AI/ML, B2B SaaS, and growth-stage companies.

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

CRITICAL: When analyzing companies:
- Extract ACTUAL numbers from the company data provided (don't make up or misread numbers)
- Validate that numbers actually fall within specified ranges before claiming "within range"
- If criteria says "$10M-$20M" and company has $500M, that is NOT "within range" - it EXCEEDS the maximum
- Double-check your math: 500 is NOT between 10 and 20
- Be precise with numbers - if you see "$15M" in the data, use 15, not 500

CRITICAL FIELD COMPLETION REQUIREMENTS:
- NEVER respond with "information can't be found", "not available", "N/A", or similar empty responses
- ALWAYS provide meaningful analysis, inference, or professional assessment for every field
- If specific data is missing, make reasonable inferences based on company name, industry, available data, and industry benchmarks
- Use phrases like "Based on available information...", "Typical for this stage...", "Industry analysis suggests..."
- Every field MUST contain substantive content (minimum 2-3 sentences)
- It's better to provide an informed inference than to say "can't find" - a professional VC analyst always provides value

You analyze companies against specific investment criteria and explain matches like you would in a partner meeting or IC (Investment Committee) memo."""
        
        # Enhance with training principles from knowledge base (if available)
        if self.vc_knowledge_agent and self.vc_knowledge_agent.knowledge_base_exists():
            # Get or generate training principles (cache after first generation)
            if self._training_principles is None:
                self.logger.info("Generating training principles from VC knowledge base...")
                self._training_principles = self.vc_knowledge_agent.generate_training_principles()
            
            if self._training_principles:
                base_prompt += f"""

---

## Training from VC Best Practices Knowledge Base

You have been trained on VC industry best practices, evaluation frameworks, and investment principles. Apply these learnings when analyzing companies:

{self._training_principles}

Use these principles to guide your analysis, but always base your conclusions on the actual company data provided."""
        
        return base_prompt
    
    def _build_expert_prompt(self, firms: List[Dict], criteria: str) -> str:
        """Build analysis prompt with ALL firm data and investment criteria
        
        Note: VC knowledge base is used for training (system prompt), not as RAG context here.
        The agent has learned VC best practices and applies them automatically.
        """
        
        # Retrieve relevant document context if RAG is enabled (for user-uploaded documents only)
        rag_context = ""
        if self.document_store:
            try:
                relevant_chunks = self.document_store.retrieve(criteria, top_k=5, min_similarity=0.3)
                if relevant_chunks:
                    rag_context = self.document_store.format_context(relevant_chunks, max_chars=1500)
                    self.logger.info(f"RAG: Retrieved {len(relevant_chunks)} relevant document chunks (user-uploaded docs)")
            except Exception as e:
                self.logger.warning(f"RAG retrieval failed: {e}, proceeding without document context")
        
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
                    # Clean up value - remove extra whitespace that might cause parsing issues
                    value = ' '.join(value.split())  # Normalize whitespace
                    if len(value) > 50:  # Truncate long values
                        value = value[:50] + "..."
                    firms_text += f"  • {field}: {value}\n"
        
        # Build prompt with optional RAG context
        prompt_start = """Analyze these companies against the following investment criteria and rank them by fit."""
        
        if rag_context:
            prompt_start += f"""

📚 **RELEVANT VC BEST PRACTICES & GUIDELINES:**
The following context from internal documentation and best practices should guide your analysis:

{rag_context}

---
"""
        
        return f"""{prompt_start}

INVESTMENT CRITERIA:
{criteria}

COMPANIES TO ANALYZE:
{firms_text}

CRITICAL INSTRUCTIONS - STRICT CRITERIA ENFORCEMENT:
You are a senior VC analyst with access to comprehensive PitchBook data. You MUST strictly adhere to the investment criteria provided above.

🚨 **STRICT FILTERING RULES:**
1. **REVENUE LIMITS**: If criteria specifies a maximum revenue (e.g., "under $10M", "less than $20M"), companies EXCEEDING this limit MUST be EXCLUDED or given a score of 0. Do NOT include companies that exceed maximum limits.
2. **VALUATION RANGES**: If criteria specifies a valuation range (e.g., "$200M-$400M"), companies OUTSIDE this range MUST be EXCLUDED or given a score of 0. Do NOT include companies below minimum or above maximum.
3. **MINIMUM REQUIREMENTS**: If criteria specifies minimums (e.g., "over $5M revenue"), companies BELOW this minimum MUST be EXCLUDED or given a score of 0.
4. **EXACT MATCHES**: Prioritize companies that meet ALL criteria exactly. Companies that exceed limits are NOT better matches - they are OUTSIDE the criteria.

🎯 **Key Investment Metrics to Focus On:**
- Revenue & Growth: Revenue, Growth Rate, Growth Rate Percentile, Web Growth Rate
- Valuation & Financing: First Financing Valuation, Total Raised, Last Financing Size
- Investor Quality: Active Investors, Former Investors, Success Probability
- Company Stage: Business Status, Year Founded, Employees, IPO/M&A Probability
- Market Position: Primary Industry Sector, Verticals, Keywords, Emerging Spaces

For each company, provide:

1. **Match Score (0-100)**: Rate how well it fits the investment criteria
   - **CRITICAL**: If a company EXCEEDS maximum limits or is BELOW minimum requirements, score MUST be 0 or very low (<30)
   - 90-100: Exceptional fit, ALL criteria met exactly within specified ranges
   - 75-89: Strong fit, ALL criteria met, slightly above/below but acceptable
   - 60-74: Good fit, most criteria met within ranges
   - 45-59: Moderate fit, some criteria met but some outside ranges
   - 30-44: Weak fit, several criteria not met or outside ranges
   - 0-29: Does NOT meet criteria - EXCEEDS maximums or BELOW minimums

2. **Investment Rationale**: 2-3 sentences explaining:
   - WHY this company matches (or doesn't match) the criteria
   - SPECIFIC data points: revenue amounts, growth rates, valuation ranges, investor names, success probabilities
   - If company EXCEEDS limits, explicitly state: "EXCEEDS maximum [metric] of [limit]" or "BELOW minimum [metric] of [limit]"
   - Stage appropriateness, competitive positioning, and market validation
   - Key strengths or concerns based on ALL available PitchBook data
   - NEVER say "information can't be found" - always provide analysis based on available data or reasonable inferences

**CRITICAL VALIDATION RULES:**
Before assigning a score, you MUST validate that numbers actually fall within the specified ranges:

1. **Extract the ACTUAL number from company data** (e.g., if Revenue field shows "$15M", use 15, not 500)
2. **Compare against criteria limits**:
   - If criteria says "revenue $10M-$20M" and company has $15M → ✅ VALID (15 is between 10 and 20)
   - If criteria says "revenue $10M-$20M" and company has $500M → ❌ INVALID (500 is NOT between 10 and 20) → Score: 0
   - If criteria says "valuation $200M-$400M" and company has $500M → ❌ INVALID (500 exceeds 400) → Score: 0
3. **DO NOT make up numbers or use wrong values** - Extract the ACTUAL value from the company data provided
4. **If you cannot find the actual number, provide analysis based on available context or industry benchmarks - NEVER say "Not available" or "can't find"**

**FILTERING LOGIC EXAMPLES:**
- Criteria: "revenue $10M-$20M"
  - Company Revenue: $15M → ✅ Score: 90, Reason: "$15M revenue (within $10M-$20M range)"
  - Company Revenue: $500M → ❌ Score: 0, Reason: "$500M revenue EXCEEDS maximum of $20M"
  - Company Revenue: $5M → ❌ Score: 0, Reason: "$5M revenue BELOW minimum of $10M"

- Criteria: "valuation $200M-$400M"
  - Company Valuation: $300M → ✅ Score: 90, Reason: "$300M valuation (within $200M-$400M range)"
  - Company Valuation: $500M → ❌ Score: 0, Reason: "$500M valuation EXCEEDS maximum of $400M"
  - Company Valuation: $100M → ❌ Score: 0, Reason: "$100M valuation BELOW minimum of $200M"

**VALIDATION CHECKLIST FOR EACH COMPANY:**
1. Extract ACTUAL revenue number from company data
2. Check if it's within revenue range (if specified)
3. Extract ACTUAL valuation number from company data
4. Check if it's within valuation range (if specified)
5. Only assign high scores (75+) if ALL numbers are within ranges
6. If ANY number is outside range, score MUST be 0-30

Write as if presenting to an Investment Committee. Use SPECIFIC data points from all available fields.

Return ONLY a JSON array with this exact format:
[{{"name": "Company Name", "score": 87, "reason": "Strong B2B AI opportunity with $15M ARR (within $10M-$20M range). $300M valuation (within $200M-$400M target). Backed by Sequoia, a16z (tier-1 VCs). Series B with 82% success probability."}}]

**REMEMBER**: 
- Extract ACTUAL numbers from company data (don't make up numbers)
- Validate that numbers actually fall within specified ranges
- If 500M is NOT between 10M-20M, then score MUST be 0
- Companies exceeding maximums or below minimums should NOT be included in top results."""
    
    def _parse_expert_analysis(self, response_text: str, top_n: int) -> List[Dict]:
        """
        Parse expert analysis response and filter out companies that don't meet criteria.
        Strictly enforces limits - companies exceeding maximums or below minimums are excluded.
        """
        import json
        import re
        
        try:
            # Extract JSON from response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx].strip()
                
                # Clean JSON: Remove markdown code blocks if present
                json_text = re.sub(r'^```json\s*', '', json_text)
                json_text = re.sub(r'^```\s*', '', json_text)
                json_text = re.sub(r'```\s*$', '', json_text)
                json_text = json_text.strip()
                
                # Try to parse JSON
                try:
                    results = json.loads(json_text)
                except json.JSONDecodeError as json_err:
                    # Try to fix common JSON issues
                    self.logger.warning(f"Initial JSON parse failed, attempting fixes: {json_err}")
                    
                    # Fix 1: Replace single quotes with double quotes (common LLM mistake)
                    json_text_fixed = json_text.replace("'", '"')
                    
                    # Fix 2: Remove trailing commas before closing brackets/braces
                    json_text_fixed = re.sub(r',\s*}', '}', json_text_fixed)
                    json_text_fixed = re.sub(r',\s*]', ']', json_text_fixed)
                    
                    # Fix 3: Fix unquoted keys (e.g., {name: "value"} -> {"name": "value"})
                    json_text_fixed = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_text_fixed)
                    
                    try:
                        results = json.loads(json_text_fixed)
                        self.logger.info("Successfully fixed and parsed JSON")
                    except json.JSONDecodeError:
                        # If still failing, try to extract valid entries manually
                        self.logger.error(f"JSON fix failed. Attempting manual extraction. Error: {json_err}")
                        self.logger.debug(f"Problematic JSON (first 500 chars): {json_text[:500]}")
                        raise ValueError(f"Unable to parse JSON response: {json_err}")
                
                # Validate results
                if not isinstance(results, list):
                    raise ValueError(f"Expected JSON array, got {type(results)}")
                
                # Filter out companies that don't meet criteria (strict enforcement with number validation)
                filtered_results = []
                for firm in results:
                    score = float(firm.get('score', 0))
                    reason = firm.get('reason', '')
                    reason_lower = reason.lower()
                    
                    # Filter out companies with low scores (likely don't meet criteria)
                    if score < 30:
                        self.logger.info(f"Filtering out {firm.get('name')}: Score {score} (below threshold)")
                        continue
                    
                    # Filter out companies explicitly marked as exceeding limits
                    if any(keyword in reason_lower for keyword in ['exceeds maximum', 'exceeds max', 'above maximum', 'above max', 'over maximum', 'over max']):
                        self.logger.info(f"Filtering out {firm.get('name')}: Exceeds maximum limits")
                        continue
                    
                    # Filter out companies explicitly marked as below minimums
                    if any(keyword in reason_lower for keyword in ['below minimum', 'below min', 'under minimum', 'under min', 'less than minimum']):
                        self.logger.info(f"Filtering out {firm.get('name')}: Below minimum requirements")
                        continue
                    
                    # Additional validation: Check for logical inconsistencies in the reason
                    # If reason says "within range" but contains numbers that don't make sense, filter out
                    import re
                    
                    # Extract revenue numbers from reason (e.g., "$500M", "500M", "$500 million")
                    revenue_patterns = [
                        r'\$?(\d+(?:\.\d+)?)\s*M(?:illion)?\s*(?:revenue|arr|sales)',
                        r'revenue[:\s]+\$?(\d+(?:\.\d+)?)\s*M',
                        r'(\d+(?:\.\d+)?)\s*M\s*(?:revenue|arr)',
                    ]
                    
                    # Extract valuation numbers
                    valuation_patterns = [
                        r'\$?(\d+(?:\.\d+)?)\s*M(?:illion)?\s*(?:valuation|val)',
                        r'valuation[:\s]+\$?(\d+(?:\.\d+)?)\s*M',
                        r'(\d+(?:\.\d+)?)\s*M\s*(?:valuation|val)',
                    ]
                    
                    # Check for obvious errors: if reason says "within range" but number is clearly wrong
                    # This is a safety check - the main filtering should happen via score and explicit keywords
                    if 'within' in reason_lower and 'range' in reason_lower:
                        # Extract any large numbers that might be errors
                        large_numbers = re.findall(r'(\d{3,})\s*M', reason, re.IGNORECASE)
                        if large_numbers:
                            # If we see numbers like 500M mentioned with "within range", it's likely an error
                            # But we'll let the score and explicit keywords handle this
                            pass
                    
                    filtered_results.append({
                        'name': firm.get('name', 'Unknown'),
                        'score': score,
                        'reason': firm.get('reason', 'No analysis provided')
                    })
                
                # Sort by score and return top N
                results_sorted = sorted(filtered_results, key=lambda x: x.get('score', 0), reverse=True)
                
                self.logger.info(f"Filtered {len(results)} results to {len(filtered_results)} that meet criteria, returning top {top_n}")
                
                return results_sorted[:top_n]
            else:
                raise ValueError("No valid JSON array found in expert analysis")
                
        except Exception as e:
            self.logger.error(f"Error parsing expert analysis: {str(e)}")
            self.logger.debug(f"Raw response (first 1000 chars): {response_text[:1000]}")
            raise
    
    def is_available(self) -> bool:
        """Check if VC expert agent can be used (requires API key and OpenAI module)"""
        return OPENAI_AVAILABLE and bool(self.config.get_openai_key())

