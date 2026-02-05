"""
Main scraper service that orchestrates all scrapers
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .config import SCRAPER_SETTINGS, COMPANY_FILTERS
from .validator import CompanyValidator
from .sources.yc_scraper import YCScraper
from .sources.open_data import OpenDataScraper
from .sources.funding_news import FundingNewsScraper
from ..models import ScrapedCompany, DataSource, ScrapeJob

logger = logging.getLogger(__name__)


class ScraperService:
    """Main service for scraping companies"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = CompanyValidator(COMPANY_FILTERS)
        self.config = SCRAPER_SETTINGS
        
        # Initialize scrapers
        self.scrapers = {
            "yc": YCScraper(self.config),
            "open_data": OpenDataScraper(self.config),
            "funding_news": FundingNewsScraper(self.config),
        }
    
    def run_scrape(self, source_names: Optional[List[str]] = None, job_type: str = "on_demand", limit: Optional[int] = None) -> ScrapeJob:
        """
        Run scraping job
        
        Args:
            source_names: List of source names to scrape (None = all)
            job_type: 'scheduled', 'on_demand', 'full_refresh'
            limit: Optional limit on number of companies to process (for testing)
            
        Returns:
            ScrapeJob instance
        """
        # Create job record
        job = ScrapeJob(
            status="running",
            job_type=job_type,
            source_name=", ".join(source_names) if source_names else "all",
            started_at=datetime.now(),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        try:
            companies_found = 0
            companies_added = 0
            companies_updated = 0
            
            sources_to_scrape = source_names or list(self.scrapers.keys())
            
            logger.info(f"Starting scrape job {job.id} for sources: {sources_to_scrape}, limit={limit}")
            
            for source_name in sources_to_scrape:
                if source_name not in self.scrapers:
                    logger.warning(f"Unknown source: {source_name}")
                    continue
                
                scraper = self.scrapers[source_name]
                
                try:
                    # Scrape
                    logger.info(f"Scraping from {source_name}...")
                    raw_companies = scraper.scrape()
                    logger.info(f"Scraped {len(raw_companies)} raw companies from {source_name}")
                    
                    # Apply limit if specified (for testing)
                    if limit is not None and len(raw_companies) > limit:
                        raw_companies = raw_companies[:limit]
                        logger.info(f"Limited to {limit} companies for testing")
                    
                    companies_found += len(raw_companies)
                    
                    # Validate
                    logger.info(f"Validating {len(raw_companies)} companies...")
                    validated = self.validator.validate(raw_companies)
                    logger.info(f"Validated {len(validated)}/{len(raw_companies)} companies passed filters")
                    
                    if validated:
                        logger.info(f"First validated company: {validated[0].get('name', 'N/A')}")
                    
                    # Get or create data source
                    data_source = self._get_or_create_source(source_name)
                    
                    # Save companies
                    for idx, company_data in enumerate(validated):
                        logger.info(f"Processing company {idx+1}/{len(validated)}: {company_data.get('name', 'N/A')}")
                        added, updated = self._save_company(company_data, data_source.id, job.id)
                        if added:
                            companies_added += 1
                            logger.info(f"✓ Added: {company_data.get('name')}")
                        if updated:
                            companies_updated += 1
                            logger.info(f"✓ Updated: {company_data.get('name')}")
                            
                except Exception as e:
                    logger.error(f"Error scraping {source_name}: {e}", exc_info=True)
                    job.errors = (job.errors or "") + f"{source_name}: {str(e)}\n"
            
            # Update job
            job.status = "completed"
            job.completed_at = datetime.now()
            job.companies_found = companies_found
            job.companies_added = companies_added
            job.companies_updated = companies_updated
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error in scrape job: {e}")
            job.status = "failed"
            job.completed_at = datetime.now()
            job.errors = str(e)
            self.db.commit()
        
        return job
    
    def _get_or_create_source(self, source_name: str) -> DataSource:
        """Get or create data source"""
        source = self.db.query(DataSource).filter(DataSource.source_name == source_name).first()
        
        if not source:
            source = DataSource(
                source_name=source_name,
                source_type="scraper",
                is_active=True,
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        
        # Update last_scraped
        source.last_scraped = datetime.now()
        self.db.commit()
        
        return source
    
    def _save_company(self, company_data: Dict[str, Any], source_id: int, job_id: int) -> tuple[bool, bool]:
        """
        Save company to database
        
        Returns:
            (added, updated) tuple
        """
        name = company_data.get("name")
        if not name:
            return False, False
        
        # Check if exists
        existing = self.db.query(ScrapedCompany).filter(
            ScrapedCompany.name.ilike(name)
        ).first()
        
        if existing:
            # Update existing
            existing.description = company_data.get("description") or existing.description
            existing.industry = company_data.get("industry") or existing.industry
            existing.stage = company_data.get("stage") or existing.stage
            existing.valuation = company_data.get("valuation") or existing.valuation
            existing.key_investors = company_data.get("key_investors") or existing.key_investors
            existing.location = company_data.get("location") or existing.location
            existing.raw_data = company_data.get("raw_data") or existing.raw_data
            existing.match_reasoning = company_data.get("match_reasoning") or existing.match_reasoning
            existing.updated_at = datetime.now()
            self.db.commit()
            return False, True
        else:
            # Create new
            company = ScrapedCompany(
                name=name,
                description=company_data.get("description"),
                industry=company_data.get("industry"),
                stage=company_data.get("stage"),
                valuation=company_data.get("valuation"),
                key_investors=company_data.get("key_investors"),
                location=company_data.get("location"),
                website=company_data.get("website"),
                linkedin_url=company_data.get("linkedin_url"),
                data_source_id=source_id,
                scrape_job_id=job_id,
                raw_data=company_data.get("raw_data"),
                match_reasoning=company_data.get("match_reasoning"),
                is_validated=True,
            )
            self.db.add(company)
            self.db.commit()
            return True, False
