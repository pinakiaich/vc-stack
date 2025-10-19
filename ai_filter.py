import pandas as pd
import openai
from typing import List, Dict, Any
import json
import logging
from config import Config
from vc_expert_agent import VCExpertAgent

class AIFilter:
    """AI-powered firm filtering using heuristics"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._setup_openai()
        # Initialize VC expert agent
        self.vc_expert = VCExpertAgent(config)
    
    def _setup_openai(self):
        """Initialize OpenAI client"""
        openai.api_key = self.config.get_openai_key()
    
    def filter_firms(self, df: pd.DataFrame, heuristics: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Filter firms based on heuristics using AI
        
        Args:
            df: DataFrame with firm data
            heuristics: User-defined filtering criteria
            top_n: Number of top firms to return
            
        Returns:
            List of filtered firm results with scores and reasons
        """
        api_key = self.config.get_openai_key()
        
        if not api_key:
            self.logger.info("No API key available, using fallback filter")
            return self._fallback_filter(df, heuristics, top_n)
        
        try:
            # Prepare firm data for VC expert analysis
            firm_data = self._prepare_firm_data(df)
            
            # Check if VC Expert is available
            if not self.vc_expert.is_available():
                self.logger.warning("VC Expert Agent not available - using fallback")
                return self._fallback_filter(df, heuristics, top_n)
            
            # Use VC Expert Agent for professional analysis
            self.logger.info("Using VC Expert Agent for analysis")
            expert_results = self.vc_expert.analyze_firms(firm_data, heuristics, top_n)
            self.logger.info(f"VC Expert analysis complete - {len(expert_results)} results")
            
            return expert_results
            
        except ImportError as e:
            self.logger.error(f"VC Expert Agent missing dependency: {str(e)}")
            self.logger.info("Falling back to keyword matching")
            print(f"❌ VC EXPERT ERROR (Import): {str(e)}")  # Console output
            return self._fallback_filter(df, heuristics, top_n)
        except ValueError as e:
            self.logger.error(f"VC Expert Agent configuration issue: {str(e)}")
            self.logger.info("Falling back to keyword matching")
            print(f"❌ VC EXPERT ERROR (Config): {str(e)}")  # Console output
            return self._fallback_filter(df, heuristics, top_n)
        except Exception as e:
            self.logger.error(f"Error in VC Expert analysis: {str(e)}")
            self.logger.info("Falling back to keyword matching")
            print(f"❌ VC EXPERT ERROR: {type(e).__name__}: {str(e)}")  # Console output
            import traceback
            traceback.print_exc()  # Full error trace
            # Return fallback with error info
            return self._fallback_filter(df, heuristics, top_n)
    
    def _prepare_firm_data(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Convert DataFrame to list of firm dictionaries"""
        firms = []
        
        for _, row in df.iterrows():
            firm = {
                'name': str(row.get('name', 'Unknown')),
                'description': str(row.get('description', 'No description')),
                'stage': str(row.get('stage', 'Unknown')),
                'revenue': str(row.get('revenue', 'Unknown')),
                'industry': str(row.get('industry', 'Unknown')),
                'location': str(row.get('location', 'Unknown'))
            }
            firms.append(firm)
        
        return firms
    
    def _analyze_with_ai(self, firms: List[Dict], heuristics: str) -> List[Dict]:
        """Use OpenAI to analyze firms against heuristics"""
        try:
            prompt = self._build_analysis_prompt(firms, heuristics)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content
            return self._parse_ai_response(result_text)
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def _build_analysis_prompt(self, firms: List[Dict], heuristics: str) -> str:
        """Build prompt for AI analysis"""
        firms_text = "\n".join([
            f"Name: {f['name']}\n"
            f"Description: {f['description']}\n"
            f"Stage: {f['stage']}\n"
            f"Revenue: {f['revenue']}\n"
            f"Industry: {f['industry']}\n"
            f"Location: {f['location']}\n---"
            for f in firms
        ])
        
        return f"""
        Analyze these firms based on the specific heuristics provided and rank them.
        
        USER'S HEURISTICS: {heuristics}
        
        FIRMS TO ANALYZE:
        {firms_text}
        
        For each firm, provide:
        1. Match score (0-100) - How well it matches the specific heuristics
        2. Detailed reason - Explain WHY it matches, referencing specific parts of the heuristics
        
        Example reason: "Matches B2B AI criteria with $8M revenue (exceeds $5M requirement), $280M valuation (within $200-400M range), Series B stage (as specified), backed by Sequoia (top-tier VC as required)"
        
        Return as JSON array with format:
        [{{"name": "firm_name", "score": 85, "reason": "detailed explanation of match against heuristics"}}]
        
        Important: Make reasons specific to the user's heuristics, not generic.
        """
    
    def _parse_ai_response(self, response_text: str) -> List[Dict]:
        """Parse AI response into structured data"""
        try:
            # Extract JSON from response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_text = response_text[start_idx:end_idx]
                return json.loads(json_text)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {str(e)}")
            raise
    
    def _rank_firms(self, ai_results: List[Dict], top_n: int) -> List[Dict]:
        """Rank firms by score and return top N"""
        # Sort by score descending
        ranked = sorted(ai_results, key=lambda x: x.get('score', 0), reverse=True)
        
        # Return top N with formatted results
        return [
            {
                'name': firm.get('name', 'Unknown'),
                'score': float(firm.get('score', 0)),
                'reason': firm.get('reason', 'No reason provided')
            }
            for firm in ranked[:top_n]
        ]
    
    def _fallback_filter(self, df: pd.DataFrame, heuristics: str, top_n: int) -> List[Dict]:
        """Fallback filtering when AI is unavailable"""
        self.logger.warning("Using fallback filtering")
        
        # Simple keyword matching
        heuristics_lower = heuristics.lower()
        keywords = [word for word in heuristics_lower.split() if len(word) > 2]  # Filter out short words
        matches = []
        
        for _, row in df.iterrows():
            score = 0
            reason_details = []
            matched_keywords = set()
            
            # Get all text fields
            name = str(row.get('name', '')).lower()
            description = str(row.get('description', '')).lower()
            industry = str(row.get('industry', '')).lower()
            stage = str(row.get('stage', '')).lower()
            location = str(row.get('location', '')).lower()
            revenue = str(row.get('revenue', '')).lower()
            
            # Track which keywords matched in which fields
            field_matches = {
                'industry': [],
                'revenue': [],
                'stage': [],
                'description': [],
                'location': [],
                'name': []
            }
            
            # Check each keyword across all fields
            for keyword in keywords:
                if keyword in industry:
                    score += 25
                    field_matches['industry'].append(keyword)
                    matched_keywords.add(keyword)
                
                if keyword in revenue:
                    score += 20
                    field_matches['revenue'].append(keyword)
                    matched_keywords.add(keyword)
                
                if keyword in stage:
                    score += 15
                    field_matches['stage'].append(keyword)
                    matched_keywords.add(keyword)
                
                if keyword in description:
                    score += 15
                    field_matches['description'].append(keyword)
                    matched_keywords.add(keyword)
                
                if keyword in location:
                    score += 10
                    field_matches['location'].append(keyword)
                    matched_keywords.add(keyword)
                
                if keyword in name:
                    score += 20
                    field_matches['name'].append(keyword)
                    matched_keywords.add(keyword)
            
            # Build detailed reason
            if matched_keywords:
                for field, kws in field_matches.items():
                    if kws:
                        actual_value = str(row.get(field, '')).strip()
                        if actual_value and actual_value != 'nan' and len(actual_value) > 0:
                            kw_str = "', '".join(kws[:2])  # Show up to 2 keywords
                            if field == 'industry':
                                reason_details.append(f"{field.capitalize()}: '{actual_value}' (matches '{kw_str}')")
                            elif field == 'revenue':
                                reason_details.append(f"Revenue: {actual_value}")
                            elif field == 'stage':
                                reason_details.append(f"Stage: {actual_value}")
                            elif field == 'description' and len(reason_details) < 3:
                                # Include a snippet of description
                                snippet = actual_value[:80] + '...' if len(actual_value) > 80 else actual_value
                                reason_details.append(f"Description mentions '{kw_str}'")
                
                if not reason_details:
                    reason_details = ["Matches search keywords"]
            else:
                reason_details = ["No strong keyword matches found"]
                score = 1  # Minimal score
            
            # Combine reason parts
            reason = '; '.join(reason_details[:4])  # Show up to 4 details
            
            matches.append({
                'name': row.get('name', 'Unknown'),
                'score': min(score, 100),  # Cap at 100
                'reason': reason if reason else "General match"
            })
        
        # Sort by score and return top N
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:top_n]
