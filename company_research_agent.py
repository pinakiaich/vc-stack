"""
Company Research Agent
Performs internet research on companies and returns structured information
"""
import logging
import json
from typing import Dict, Optional, List
import requests
from bs4 import BeautifulSoup
from config import Config

# Try to import DuckDuckGo search (optional)
try:
    from duckduckgo_search import DDGS
    DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False

# Try to import OpenAI
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


class CompanyResearchAgent:
    """Agent that performs internet research on companies"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logger
        # Get OpenAI key - check both config and session state
        self.openai_key = config.get_openai_key()
        if not self.openai_key:
            # Try to get from session state if available (for Streamlit context)
            try:
                import streamlit as st
                if hasattr(st, 'session_state') and 'openai_key' in st.session_state:
                    self.openai_key = st.session_state.get('openai_key')
                    self.logger.info("Using OpenAI key from Streamlit session state")
            except:
                pass
        
        if self.openai_key:
            self.logger.info("OpenAI key available for research synthesis")
        else:
            self.logger.warning("No OpenAI key available - will use basic research mode")
        
    def research_company(
        self, 
        company_name: str,
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """
        Research a company and return structured information
        
        Args:
            company_name: Name of the company to research
            additional_info: Optional dict with additional info (industry, description, etc.)
            
        Returns:
            Dict with research findings:
            - company_name
            - country_of_incorporation
            - industry
            - industry_background (200 words)
            - company_background
            - founder_profile
            - competition
        """
        self.logger.info(f"Researching company: {company_name}")
        
        # Step 1: Search for company information
        search_results = self._search_company(company_name, additional_info)
        
        # Step 2: Extract and synthesize information
        research_data = self._synthesize_research(company_name, search_results, additional_info)
        
        return research_data
    
    def _search_company(self, company_name: str, additional_info: Optional[Dict] = None) -> List[Dict]:
        """Search for company information using DuckDuckGo or web scraping"""
        search_results = []
        
        industry = additional_info.get('industry', '') if additional_info else ''
        vertical = additional_info.get('vertical', '') if additional_info else ''
        description = additional_info.get('description', '') if additional_info else ''
        
        # Parse industry hierarchy for more specific searches
        try:
            from industry_hierarchy_agent import IndustryHierarchyAgent
            hierarchy_agent = IndustryHierarchyAgent()
            hierarchy = hierarchy_agent.parse_industry_hierarchy(industry, vertical, description)
            
            # Get specific search terms (most specific first)
            specific_terms = hierarchy_agent.get_specific_search_terms(hierarchy)
            industry_full = hierarchy.get('industry_full', industry)
            industry_specific = hierarchy.get('industry_specific', '')
            industry_niche = hierarchy.get('industry_niche', '')
        except Exception as e:
            self.logger.warning(f"Could not parse industry hierarchy: {e}")
            hierarchy = {}
            specific_terms = [industry] if industry else []
            industry_full = industry
            industry_specific = ''
            industry_niche = ''
        
        # Build comprehensive search queries with focus on quantitative data
        queries = [
            # Basic company info
            f"{company_name} company",
            f"{company_name} startup",
            
            # Quantitative data queries
            f"{company_name} revenue funding valuation million billion",
            f"{company_name} market size TAM SAM billion",
            f"{company_name} market share percentage",
            f"{company_name} growth rate CAGR percentage",
            
            # Founder details
            f"{company_name} founders CEO LinkedIn",
            f"{company_name} founder background previous companies",
            
            # Location and incorporation
            f"{company_name} location headquarters country incorporated",
            
            # Competitive landscape
            f"{company_name} competitors market analysis",
            f"{company_name} competitive landscape",
        ]
        
        # Add industry-specific quantitative queries (use most specific term first)
        if specific_terms:
            # Use most specific term (niche) for targeted searches
            most_specific = specific_terms[0] if specific_terms else industry
            
            queries.extend([
                # Most specific searches (e.g., "GPUs" instead of "IT")
                f"{company_name} {most_specific} market size billion",
                f"{company_name} {most_specific} market report 2024 2025",
                f"{company_name} {most_specific} growth forecast CAGR",
                f"{most_specific} market size TAM SAM billion 2024",
                f"{most_specific} industry growth rate CAGR forecast",
                f"{most_specific} market report statistics",
            ])
            
            # Also add broader industry searches for context
            if industry and industry.lower() != most_specific.lower():
                queries.extend([
                    f"{company_name} {industry} market size billion",
                    f"{industry} market size TAM SAM billion 2024",
                ])
        elif industry:
            # Fallback to original industry-based queries
            queries.extend([
                f"{company_name} {industry} market size billion",
                f"{company_name} {industry} market report 2024 2025",
                f"{company_name} {industry} growth forecast CAGR",
                f"{industry} market size TAM SAM billion 2024",
                f"{industry} industry growth rate CAGR forecast",
                f"{industry} market report statistics",
            ])
        
        # Add queries targeting high-quality research sources
        # These will help find quantitative data from research sites
        research_queries = [
            f"{company_name} Crunchbase",
            f"{company_name} TechCrunch funding",
            f"{company_name} VentureBeat",
        ]
        
        # Use most specific industry term for research queries
        research_industry = specific_terms[0] if specific_terms else industry
        
        if research_industry:
            research_queries.extend([
                f"{research_industry} market size Statista",
                f"{research_industry} market report Gartner",
                f"{research_industry} industry analysis McKinsey",
                f"{research_industry} market forecast Grand View Research",
            ])
            
            # Also add broader industry for comprehensive coverage
            if industry and industry.lower() != research_industry.lower():
                research_queries.extend([
                    f"{industry} market size Statista",
                    f"{industry} market report Gartner",
                ])
        
        queries.extend(research_queries)
        
        # Try DuckDuckGo search first (free, no API key)
        if DDG_AVAILABLE:
            try:
                self.logger.info(f"Using DuckDuckGo search with {len(queries)} queries for quantitative data")
                with DDGS() as ddgs:
                    # Prioritize quantitative queries first
                    quantitative_queries = [q for q in queries if any(term in q.lower() for term in ['revenue', 'funding', 'market', 'size', 'growth', 'cagr', 'tam', 'sam', 'billion', 'million'])]
                    other_queries = [q for q in queries if q not in quantitative_queries]
                    
                    # Search quantitative queries first (more important)
                    for query in quantitative_queries[:10]:  # Increased from 8 to 10
                        try:
                            results = list(ddgs.text(query, max_results=5))
                            if results:
                                search_results.extend(results)
                                self.logger.info(f"Query '{query}': Found {len(results)} results")
                            else:
                                self.logger.warning(f"Query '{query}': No results found")
                        except Exception as e:
                            self.logger.warning(f"DuckDuckGo search failed for '{query}': {e}")
                            # Continue with next query instead of failing completely
                            continue
                    
                    # Then search other queries
                    for query in other_queries[:8]:  # Increased from 5 to 8
                        try:
                            results = list(ddgs.text(query, max_results=3))
                            if results:
                                search_results.extend(results)
                                self.logger.info(f"Query '{query}': Found {len(results)} results")
                        except Exception as e:
                            self.logger.warning(f"DuckDuckGo search failed for '{query}': {e}")
                            continue
                    
                self.logger.info(f"Total search results collected: {len(search_results)}")
                
                # Remove duplicates based on URL
                seen_urls = set()
                unique_results = []
                for result in search_results:
                    url = result.get('href', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        unique_results.append(result)
                
                search_results = unique_results
                self.logger.info(f"After deduplication: {len(search_results)} unique results")
                
            except Exception as e:
                self.logger.error(f"DuckDuckGo search error: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
        else:
            self.logger.warning("DuckDuckGo not available - install with: pip install duckduckgo-search")
        
        # Fallback: Try to scrape company website if available in additional_info
        if additional_info and additional_info.get('website'):
            try:
                website_content = self._scrape_website(additional_info['website'])
                if website_content:
                    search_results.append({
                        'title': f"{company_name} - Official Website",
                        'body': website_content,
                        'href': additional_info['website']
                    })
            except Exception as e:
                self.logger.warning(f"Failed to scrape website: {e}")
        
        return search_results
    
    def _scrape_website(self, url: str) -> Optional[str]:
        """Scrape text content from a website"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            # Extract text
            text = soup.get_text(separator='\n', strip=True)
            # Limit text length
            return text[:5000]  # First 5000 chars
        except Exception as e:
            self.logger.warning(f"Failed to scrape {url}: {e}")
            return None
    
    def _synthesize_research(
        self, 
        company_name: str, 
        search_results: List[Dict],
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """Synthesize search results into structured research data"""
        
        # Check OpenAI availability
        has_openai_key = bool(self.openai_key)
        openai_available = OPENAI_AVAILABLE
        
        self.logger.info(f"OpenAI key present: {has_openai_key}, OpenAI module available: {openai_available}")
        
        # If OpenAI is available, use it to synthesize (even with minimal search results)
        if has_openai_key and openai_available:
            try:
                return self._synthesize_with_openai(company_name, search_results, additional_info)
            except Exception as e:
                self.logger.error(f"OpenAI synthesis failed: {e}, falling back to basic mode")
                # Fallback to basic if OpenAI fails
                return self._synthesize_basic(company_name, search_results, additional_info)
        else:
            # Fallback: Basic extraction from search results
            self.logger.warning(f"OpenAI not available (key: {has_openai_key}, module: {openai_available}), using basic mode")
            return self._synthesize_basic(company_name, search_results, additional_info)
    
    def _synthesize_with_openai(
        self,
        company_name: str,
        search_results: List[Dict],
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """Use OpenAI to synthesize research into structured format"""
        
        # Parse industry hierarchy for context
        industry = additional_info.get('industry', '') if additional_info else ''
        vertical = additional_info.get('vertical', '') if additional_info else ''
        description = additional_info.get('description', '') if additional_info else ''
        
        try:
            from industry_hierarchy_agent import IndustryHierarchyAgent
            hierarchy_agent = IndustryHierarchyAgent()
            hierarchy = hierarchy_agent.parse_industry_hierarchy(industry, vertical, description)
            industry_full = hierarchy.get('industry_full', industry)
            industry_specific = hierarchy.get('industry_specific', '')
            industry_niche = hierarchy.get('industry_niche', '')
        except Exception:
            hierarchy = {}
            industry_full = industry
            industry_specific = ''
            industry_niche = ''
        
        # Prepare context from search results
        context = ""
        if not search_results:
            self.logger.warning("No search results available, but proceeding with OpenAI synthesis")
            context = f"Limited information available. Company name: {company_name}"
            if additional_info:
                if industry_full:
                    context += f"\nKnown industry (full hierarchy): {industry_full}"
                elif additional_info.get('industry'):
                    context += f"\nKnown industry: {additional_info['industry']}"
                if industry_specific:
                    context += f"\nSpecific sub-industry: {industry_specific}"
                if industry_niche:
                    context += f"\nNiche/vertical: {industry_niche}"
                if additional_info.get('sector'):
                    context += f"\nKnown sector: {additional_info['sector']}"
                if additional_info.get('stage'):
                    context += f"\nKnown funding stage: {additional_info['stage']}"
        else:
            # Use more results for better coverage - prioritize results with actual content
            valid_results = [r for r in search_results if r.get('body', '').strip() and len(r.get('body', '').strip()) > 50]
            
            if not valid_results:
                self.logger.warning("Search results found but all are empty or too short")
                # Use all results even if short
                valid_results = search_results
            
            # Use top 15 results (increased from 10) for better coverage
            for i, result in enumerate(valid_results[:15], 1):
                title = result.get('title', '')
                body = result.get('body', '')
                
                # Filter out very short or empty results
                if not body or len(body.strip()) < 20:
                    continue
                
                # Use more content (increased from 1500 to 2000 chars)
                body = body[:2000]
                href = result.get('href', '')
                context += f"\n\nSource {i}:\nTitle: {title}\nURL: {href}\nContent: {body}\n"
            
            self.logger.info(f"Using {len(valid_results[:15])} search results for synthesis")
        
        # Add additional info if available
        additional_context = ""
        if additional_info:
            if additional_info.get('industry'):
                additional_context += f"\nKnown industry: {additional_info['industry']}"
            if additional_info.get('description'):
                additional_context += f"\nKnown description: {additional_info['description']}"
        
        # Add hierarchy instructions to prompt
        hierarchy_instructions = ""
        if industry_niche:
            hierarchy_instructions = f"""

CRITICAL INDUSTRY HIERARCHY UNDERSTANDING:
- The company operates in: {industry_full}
- Focus research on the SPECIFIC niche: {industry_niche}
- For industry background, discuss {industry_niche} market specifically (e.g., GPU market, not just IT market)
- For market size, use {industry_niche} market numbers (e.g., GPU market size, not IT market size)
- For competition, list competitors in {industry_niche} (e.g., other GPU companies, not just IT companies)
- If hierarchy is "IT → Computer Hardware → GPUs", research GPUs, not just IT
"""
        
        prompt = f"""You are a professional research analyst specializing in quantitative market research. Research the company "{company_name}" based on the following search results and provide a comprehensive, data-driven research summary.

{additional_context}{hierarchy_instructions}

Search Results:
{context}

CRITICAL: Extract ALL quantitative data (numbers, percentages, dollar amounts, growth rates) from the search results. Look specifically for:
- Market size numbers (TAM, SAM in billions/millions)
- Growth rates (CAGR percentages)
- Revenue figures (in millions/billions)
- Funding amounts (in millions/billions)
- Valuation numbers
- Market share percentages
- Employee counts
- Year/date information for all numbers

Please provide a comprehensive research summary in the following JSON format:
{{
    "company_name": "{company_name}",
    "country_of_incorporation": "Country name or 'Unknown' if not found",
    "industry": "Primary industry the company operates in",
    "quantitative_data": {{
        "market_size_tam": "Total Addressable Market in $X billion/million (include year and source if available)",
        "market_size_sam": "Serviceable Addressable Market in $X billion/million (include year and source if available)",
        "market_growth_cagr": "Compound Annual Growth Rate as X% (include period, e.g., 2024-2029, and source)",
        "company_revenue": "Company revenue in $X million/billion (include year and source if available)",
        "funding_raised": "Total funding raised in $X million/billion (include rounds if available)",
        "valuation": "Company valuation in $X million/billion (include year and source if available)",
        "employee_count": "Number of employees (include year if available)",
        "market_share": "Market share as X% (include year and source if available)"
    }},
    "industry_background": "A comprehensive 200-word overview of the SPECIFIC niche/vertical industry (e.g., GPU market if hierarchy is 'IT → Computer Hardware → GPUs', NOT just IT market). Include: current market size for the SPECIFIC niche (with numbers), growth trends for the SPECIFIC niche (with percentages), key drivers in the SPECIFIC niche, future projections for the SPECIFIC niche (with CAGR if available), and market dynamics in the SPECIFIC niche. MUST include quantitative data if found in search results. Focus on the most specific level of the industry hierarchy.",
    "company_background": "Detailed background about the company including: history, business model, products/services, key milestones, and any available financial metrics. Include specific numbers (revenue, funding, employees) if found.",
    "founder_profile": "Information about the founder(s) including: full names, LinkedIn profile URLs (if mentioned), educational background, previous companies/work experience, years of experience, and notable achievements. Be specific with names and details.",
    "competition": "Overview of main competitors including: competitor names, market positioning, competitive landscape analysis, and market share comparisons (with percentages if available). Be specific with competitor names and include quantitative comparisons if found."
}}

CRITICAL REQUIREMENTS FOR QUANTITATIVE DATA:
1. Extract ALL numbers from search results - market size, growth rates, revenue, funding, etc.
2. Include units ($ billion, $ million, %, etc.) for all numbers
3. Include year/date information when available
4. Include source/citation when mentioned in search results
5. If a number is not found, use "Not available" but search ALL results first
6. Look for patterns like "$50B", "15% CAGR", "$10M revenue", "50 employees"

CRITICAL REQUIREMENTS FOR ALL FIELDS:
1. ALL fields must be filled - do NOT leave any field empty or as "Not available" unless absolutely no information exists
2. The industry_background MUST be approximately 200 words and MUST include quantitative data (market size, growth rates) if available
3. company_background MUST include specific numbers (revenue, funding, employees) if found
4. founder_profile MUST include full names, LinkedIn URLs (if mentioned), and specific details
5. competition MUST include specific competitor names and quantitative comparisons if available
6. Be specific and factual based on the search results - extract ALL available information including numbers
7. If quantitative data is truly not available, use "Not available" but try to find information from multiple sources first
8. Use the search results provided - extract information from all sources, not just one
9. Prioritize extracting numbers and quantitative metrics - this is critical for investment analysis

Return ONLY valid JSON, no additional text. Ensure ALL fields have substantial content and include quantitative data wherever possible."""

        try:
            if not self.openai_key:
                raise ValueError("OpenAI API key not available")
            
            self.logger.info(f"Using OpenAI to synthesize research for {company_name}")
            
            # Use OpenAI client (new API) if available, otherwise fallback to old API
            system_message = "You are a professional quantitative research analyst specializing in market research and financial data. Always return valid JSON. Extract ALL available information including numbers, percentages, dollar amounts, and growth rates from the search results provided. Prioritize quantitative data extraction.\n\nCRITICAL: Understand industry hierarchies. When a company is in 'Information Technology', identify the specific sub-industry (e.g., 'Computer Hardware') and niche (e.g., 'GPUs'). Research should focus on the MOST SPECIFIC industry classification, not just the broad category. For example: 'IT' → 'Computer Hardware' → 'GPUs' means research the GPU market, not just IT. Use the specific niche/vertical for market size, growth, and competitive analysis."
            
            try:
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=3000  # Increased for quantitative data extraction
                )
                response_text = response.choices[0].message.content.strip()
                self.logger.info("OpenAI synthesis successful")
            except (NameError, AttributeError):
                # Fallback to old OpenAI API
                import openai
                openai.api_key = self.openai_key
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=3000  # Increased for quantitative data extraction
                )
                response_text = response.choices[0].message.content.strip()
                self.logger.info("OpenAI synthesis successful (old API)")
            
            # Extract JSON from response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            research_data = json.loads(response_text)
            
            # Validate required fields
            required_fields = [
                'company_name', 'country_of_incorporation', 'industry',
                'industry_background', 'company_background', 'founder_profile', 'competition'
            ]
            for field in required_fields:
                if field not in research_data:
                    research_data[field] = "Not available"
            
            # Validate quantitative_data field (new structure)
            if 'quantitative_data' not in research_data:
                research_data['quantitative_data'] = {}
            
            # Ensure quantitative_data has all expected fields
            quantitative_fields = [
                'market_size_tam', 'market_size_sam', 'market_growth_cagr',
                'company_revenue', 'funding_raised', 'valuation',
                'employee_count', 'market_share'
            ]
            for field in quantitative_fields:
                if field not in research_data['quantitative_data']:
                    research_data['quantitative_data'][field] = "Not available"
            
            self.logger.info(f"Research synthesis complete with quantitative data: {sum(1 for v in research_data.get('quantitative_data', {}).values() if v and v != 'Not available')} metrics found")
            
            return research_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse OpenAI JSON response: {e}")
            self.logger.error(f"Response was: {response_text[:500]}")
            # Try to fix JSON and retry once
            try:
                import re
                # Fix common JSON issues
                fixed_text = response_text.replace("'", '"')
                fixed_text = re.sub(r',\s*}', '}', fixed_text)
                fixed_text = re.sub(r',\s*]', ']', fixed_text)
                research_data = json.loads(fixed_text)
                self.logger.info("Successfully fixed and parsed JSON")
                # Validate and return
                required_fields = ['company_name', 'country_of_incorporation', 'industry', 'industry_background', 'company_background', 'founder_profile', 'competition']
                for field in required_fields:
                    if field not in research_data:
                        research_data[field] = "Not available"
                return research_data
            except:
                self.logger.error("JSON fix failed, falling back to basic mode")
                return self._synthesize_basic(company_name, search_results, additional_info)
        except Exception as e:
            self.logger.error(f"OpenAI synthesis failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return self._synthesize_basic(company_name, search_results, additional_info)
    
    def _synthesize_basic(
        self,
        company_name: str,
        search_results: List[Dict],
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """Basic synthesis without OpenAI (fallback)"""
        self.logger.warning("Using basic research mode - OpenAI not available or failed")
        
        # Extract basic information from search results
        all_text = " ".join([r.get('body', '') for r in search_results[:5]])  # Use more results
        all_text = all_text[:5000]  # Increased limit
        
        # Basic extraction (very simple)
        industry = additional_info.get('industry', 'Unknown') if additional_info else 'Unknown'
        
        # Try to extract country from search results
        country = "Unknown"
        for result in search_results:
            body = result.get('body', '').lower()
            # Look for common country indicators
            if 'incorporated' in body or 'headquarters' in body or 'based in' in body:
                # Try to extract country name (very basic)
                import re
                country_patterns = [
                    r'(?:incorporated|headquartered|based in|located in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:incorporated|headquarters)'
                ]
                for pattern in country_patterns:
                    match = re.search(pattern, body, re.IGNORECASE)
                    if match:
                        country = match.group(1)
                        break
        
        return {
            "company_name": company_name,
            "country_of_incorporation": country,
            "industry": industry if industry != 'Unknown' else "Not available",
            "industry_background": f"Industry information for {industry} is not available in this basic mode. Please configure OpenAI API key for detailed research with comprehensive industry analysis.",
            "company_background": all_text[:800] if all_text else "Company background not available. Please configure OpenAI API key for detailed research.",
            "founder_profile": "Founder information not available in basic mode. Please configure OpenAI API key for detailed research.",
            "competition": "Competitive information not available in basic mode. Please configure OpenAI API key for detailed research."
        }
