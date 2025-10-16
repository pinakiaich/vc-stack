import pandas as pd
import openai
from typing import List, Dict, Any
import json
import logging
from config import Config

class AIFilter:
    """AI-powered firm filtering using heuristics"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._setup_openai()
    
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
        try:
            # Prepare firm data for AI analysis
            firm_data = self._prepare_firm_data(df)
            
            # Get AI analysis
            ai_results = self._analyze_with_ai(firm_data, heuristics)
            
            # Process and rank results
            ranked_firms = self._rank_firms(ai_results, top_n)
            
            return ranked_firms
            
        except Exception as e:
            self.logger.error(f"Error in AI filtering: {str(e)}")
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
        Analyze these firms based on the heuristics and rank them:
        
        HEURISTICS: {heuristics}
        
        FIRMS:
        {firms_text}
        
        For each firm, provide:
        1. Match score (0-100)
        2. Reason for the score
        
        Return as JSON array with format:
        [{{"name": "firm_name", "score": 85, "reason": "explanation"}}]
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
        matches = []
        
        for _, row in df.iterrows():
            score = 0
            reason_parts = []
            
            # Check name
            if any(word in row.get('name', '').lower() for word in heuristics_lower.split()):
                score += 20
                reason_parts.append("Name matches keywords")
            
            # Check description
            if any(word in row.get('description', '').lower() for word in heuristics_lower.split()):
                score += 30
                reason_parts.append("Description matches keywords")
            
            # Check industry
            if any(word in row.get('industry', '').lower() for word in heuristics_lower.split()):
                score += 25
                reason_parts.append("Industry matches keywords")
            
            if score > 0:
                matches.append({
                    'name': row.get('name', 'Unknown'),
                    'score': score,
                    'reason': '; '.join(reason_parts)
                })
        
        # Sort and return top N
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches[:top_n]
