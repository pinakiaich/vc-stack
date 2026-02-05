"""
Research Validation Agent
Cross-checks that all required research fields are present and complete
"""
import logging
from typing import Dict, List, Optional
from config import Config

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    try:
        import openai
        OPENAI_AVAILABLE = True
    except ImportError:
        OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class ResearchValidationAgent:
    """Agent that validates research completeness and quality"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logger
        self.openai_key = config.get_openai_key() if OPENAI_AVAILABLE else None
        
    def validate_research(self, research_data: Dict, company_name: str) -> Dict:
        """
        Validate that research contains all required fields and is complete
        
        Args:
            research_data: Research data dictionary
            company_name: Name of the company being researched
            
        Returns:
            Dict with validation results:
            - is_complete: bool
            - missing_fields: List[str]
            - quality_score: float (0-1)
            - recommendations: List[str]
        """
        required_fields = [
            'company_name',
            'country_of_incorporation',
            'industry',
            'industry_background',
            'company_background',
            'founder_profile',
            'competition'
        ]
        
        # Check for quantitative_data field (new requirement)
        quantitative_fields = []
        if 'quantitative_data' in research_data:
            quantitative_data = research_data.get('quantitative_data', {})
            if isinstance(quantitative_data, dict):
                # Check if any quantitative fields have actual data
                has_quantitative_data = any(
                    v and v != "Not available" and str(v).strip() 
                    for v in quantitative_data.values()
                )
                if not has_quantitative_data:
                    quantitative_fields = ['quantitative_data']
        else:
            quantitative_fields = ['quantitative_data']
        
        missing_fields = []
        empty_fields = []
        
        for field in required_fields:
            if field not in research_data:
                missing_fields.append(field)
            elif not research_data[field] or research_data[field].strip() in ['', 'Not available', 'Unknown', 'N/A']:
                empty_fields.append(field)
        
        # Calculate quality score (include quantitative data in scoring)
        total_fields = len(required_fields) + 1  # Add quantitative_data as bonus field
        complete_fields = total_fields - len(missing_fields) - len(empty_fields) - len(quantitative_fields)
        quality_score = complete_fields / total_fields if total_fields > 0 else 0.0
        
        # Add quantitative fields to empty_fields for recommendations
        if quantitative_fields:
            empty_fields.extend(quantitative_fields)
        
        # Generate recommendations using AI if available
        recommendations = []
        if self.openai_key and OPENAI_AVAILABLE and (missing_fields or empty_fields):
            recommendations = self._generate_recommendations(
                company_name, research_data, missing_fields, empty_fields
            )
        else:
            # Basic recommendations
            if missing_fields:
                recommendations.append(f"Missing fields: {', '.join(missing_fields)}")
            if empty_fields:
                recommendations.append(f"Empty fields need more research: {', '.join(empty_fields)}")
        
        return {
            'is_complete': len(missing_fields) == 0 and len(empty_fields) == 0,
            'missing_fields': missing_fields,
            'empty_fields': empty_fields,
            'quality_score': quality_score,
            'recommendations': recommendations,
            'complete_fields': complete_fields,
            'total_fields': total_fields
        }
    
    def _generate_recommendations(
        self,
        company_name: str,
        research_data: Dict,
        missing_fields: List[str],
        empty_fields: List[str]
    ) -> List[str]:
        """Use AI to generate specific recommendations for improving research"""
        try:
            prompt = f"""You are a research quality analyst. Review the research data for {company_name} and provide specific recommendations.

Current Research Status:
- Missing fields: {', '.join(missing_fields) if missing_fields else 'None'}
- Empty/Incomplete fields: {', '.join(empty_fields) if empty_fields else 'None'}

Available Research Data:
- Company Name: {research_data.get('company_name', 'N/A')}
- Industry: {research_data.get('industry', 'N/A')}
- Industry Background: {'Present' if research_data.get('industry_background') and research_data.get('industry_background') not in ['Not available', 'Unknown'] else 'Missing/Empty'}
- Company Background: {'Present' if research_data.get('company_background') and research_data.get('company_background') not in ['Not available', 'Unknown'] else 'Missing/Empty'}
- Founder Profile: {'Present' if research_data.get('founder_profile') and research_data.get('founder_profile') not in ['Not available', 'Unknown'] else 'Missing/Empty'}
- Competition: {'Present' if research_data.get('competition') and research_data.get('competition') not in ['Not available', 'Unknown'] else 'Missing/Empty'}

Provide 3-5 specific, actionable recommendations for improving the research. Focus on:
1. What additional search queries would help find missing information
2. What sources to check (company website, LinkedIn, Crunchbase, news articles, etc.)
3. How to improve the quality of existing fields

Return ONLY a JSON array of recommendation strings:
["Recommendation 1", "Recommendation 2", "Recommendation 3"]

Be specific and actionable."""

            try:
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a research quality analyst. Always return valid JSON arrays."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                response_text = response.choices[0].message.content.strip()
            except (NameError, AttributeError):
                import openai
                openai.api_key = self.openai_key
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a research quality analyst. Always return valid JSON arrays."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                response_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            import json
            import re
            
            # Clean JSON
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Try to parse
            try:
                recommendations = json.loads(response_text)
                if isinstance(recommendations, list):
                    return recommendations
            except json.JSONDecodeError:
                # Try to fix common issues
                response_text = response_text.replace("'", '"')
                response_text = re.sub(r',\s*}', '}', response_text)
                response_text = re.sub(r',\s*]', ']', response_text)
                try:
                    recommendations = json.loads(response_text)
                    if isinstance(recommendations, list):
                        return recommendations
                except:
                    pass
            
            # Fallback: extract from text
            recommendations = []
            for line in response_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('"') or line.startswith("'")):
                    line = line.strip('"').strip("'")
                    if line:
                        recommendations.append(line)
            
            return recommendations if recommendations else ["Review research data and ensure all fields are populated"]
            
        except Exception as e:
            self.logger.warning(f"Failed to generate AI recommendations: {e}")
            return ["Review research data and ensure all fields are populated"]
    
    def enhance_research(self, research_data: Dict, company_name: str) -> Dict:
        """
        Attempt to enhance incomplete research by identifying gaps
        
        Args:
            research_data: Current research data
            company_name: Company name
            
        Returns:
            Enhanced research data with suggestions
        """
        validation = self.validate_research(research_data, company_name)
        
        # Add validation metadata to research data
        research_data['_validation'] = validation
        
        return research_data
