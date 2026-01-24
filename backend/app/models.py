from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .core.db import Base

class Company(Base):
    __tablename__ = "company"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text)
    stage = Column(String(100))
    revenue = Column(String(100))
    industry = Column(String(100))
    location = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    filter_results = relationship("FilterResult", back_populates="company", cascade="all, delete-orphan")

class FilterQuery(Base):
    """Store filter queries for analytics and history"""
    __tablename__ = "filter_query"
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), index=True)  # Optional user identifier
    criteria = Column(Text, nullable=False)  # Investment criteria/heuristics
    total_firms_analyzed = Column(Integer, default=0)
    processing_time_ms = Column(Integer)  # Processing time in milliseconds
    filter_method = Column(String(50))  # 'hybrid', 'vc_expert', 'keyword'
    used_cache = Column(Boolean, default=False)  # Whether cache was used
    used_rag = Column(Boolean, default=False)  # Whether RAG was used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    results = relationship("FilterResult", back_populates="query", cascade="all, delete-orphan")

class FilterResult(Base):
    __tablename__ = "filter_result"
    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey('filter_query.id'), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)  # Denormalized for easier queries
    score = Column(Float, nullable=False)
    rank = Column(Integer)  # Ranking (1-10)
    reason = Column(Text)
    vector_similarity = Column(Float)  # Vector search similarity score (if available)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    query = relationship("FilterQuery", back_populates="results")
    company = relationship("Company", back_populates="filter_results")
    feedback = relationship("UserFeedback", back_populates="result", cascade="all, delete-orphan")

class UserFeedback(Base):
    """Store user feedback on filter results for learning"""
    __tablename__ = "user_feedback"
    id = Column(Integer, primary_key=True)
    result_id = Column(Integer, ForeignKey('filter_result.id'), nullable=False, index=True)
    action = Column(String(50))  # 'selected', 'rejected', 're-ranked', 'viewed'
    user_notes = Column(Text)
    rating = Column(Integer)  # Optional rating (1-5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    result = relationship("FilterResult", back_populates="feedback")


# ============================================================================
# VC-Stack v2 Models: Deal Workspace
# ============================================================================

class Deal(Base):
    """Deal workspace - represents an investment opportunity"""
    __tablename__ = "deal"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    source = Column(String(255))  # How the deal was sourced (e.g., "referral", "outreach")
    owner = Column(String(100))  # Deal owner/analyst
    sector = Column(String(100))  # Industry sector
    stage = Column(String(100))  # Investment stage (e.g., "Series A", "Series B")
    status = Column(String(50), default="active")  # active, on_hold, passed, proceeding
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    memos = relationship("Memo", back_populates="deal", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="deal", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="deal", cascade="all, delete-orphan")
    data_room_documents = relationship("DataRoomDocument", back_populates="deal", cascade="all, delete-orphan")
    external_sources = relationship("ExternalSource", back_populates="deal", cascade="all, delete-orphan")
    research_findings = relationship("ResearchFinding", back_populates="deal", cascade="all, delete-orphan")


class Memo(Base):
    """Investment memos (screening, IC, etc.)"""
    __tablename__ = "memo"
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, ForeignKey('deal.id'), nullable=False, index=True)
    memo_type = Column(String(50), nullable=False)  # 'screening', 'ic', 'diligence'
    version = Column(Integer, default=1)
    json_payload = Column(Text)  # JSON content of the memo (can be large)
    generated_by_agent = Column(Boolean, default=True)  # Whether generated by AI agent
    confidence_score = Column(Float)  # 0-1 confidence score
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    deal = relationship("Deal", back_populates="memos")


class Risk(Base):
    """Risk register - identified risks for a deal"""
    __tablename__ = "risk"
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, ForeignKey('deal.id'), nullable=False, index=True)
    risk_type = Column(String(100))  # 'market', 'technology', 'team', 'financial', etc.
    description = Column(Text, nullable=False)
    severity = Column(String(20))  # 'low', 'medium', 'high', 'critical'
    mitigation = Column(Text)  # Mitigation strategy
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    deal = relationship("Deal", back_populates="risks")


class Decision(Base):
    """Investment decisions (proceed, hold, pass)"""
    __tablename__ = "decision"
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, ForeignKey('deal.id'), nullable=False, index=True)
    verdict = Column(String(50), nullable=False)  # 'proceed', 'hold', 'pass'
    rationale = Column(Text)  # Decision rationale
    conditions = Column(Text)  # Conditions for proceeding (if applicable)
    decided_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    deal = relationship("Deal", back_populates="decisions")


class DataRoomDocument(Base):
    """Documents uploaded to data room"""
    __tablename__ = "data_room_document"
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, ForeignKey('deal.id'), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    doc_type = Column(String(50))  # 'pdf', 'md', 'txt', 'excel', etc.
    source = Column(String(100), default="company")  # 'company', 'external', etc.
    embedding_id = Column(String(255))  # Reference to embedding/chunk ID in document store
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    deal = relationship("Deal", back_populates="data_room_documents")


class ExternalSource(Base):
    """External research sources (URLs, reports, etc.)"""
    __tablename__ = "external_source"
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, ForeignKey('deal.id'), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    source_type = Column(String(50))  # 'report', 'news', 'academic', 'database', 'other'
    embedding_id = Column(String(255), nullable=True)  # Set after ingestion
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    deal = relationship("Deal", back_populates="external_sources")


class ResearchFinding(Base):
    """Research findings from data room or external sources"""
    __tablename__ = "research_finding"
    id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, ForeignKey('deal.id'), nullable=False, index=True)
    category = Column(String(100))  # 'facts', 'metrics', 'market', 'competition', etc.
    source_type = Column(String(50))  # 'data_room', 'external', 'agent_analysis'
    content = Column(Text, nullable=False)  # The finding content
    citation = Column(String(500))  # Source citation (URL or document reference)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    deal = relationship("Deal", back_populates="research_findings")


# ============================================================================
# Company Research Agent Models
# ============================================================================

class ScrapedCompany(Base):
    """Companies scraped from public sources"""
    __tablename__ = "scraped_company"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    industry = Column(String(100), index=True)
    stage = Column(String(100), index=True)  # Series B, Series C, etc.
    valuation = Column(Float)  # Valuation in USD
    valuation_currency = Column(String(10), default="USD")
    key_investors = Column(Text)  # Comma-separated or JSON
    location = Column(String(255), index=True)
    country = Column(String(100), index=True)
    founded_date = Column(DateTime)
    employee_count = Column(Integer)
    website = Column(String(500))
    linkedin_url = Column(String(500))
    data_source_id = Column(Integer, ForeignKey('data_source.id'), index=True)
    scrape_job_id = Column(Integer, ForeignKey('scrape_job.id'), index=True)
    raw_data = Column(JSON)  # Store original scraped data
    is_validated = Column(Boolean, default=False)  # Passed filter criteria
    match_reasoning = Column(Text)  # Why this company matched the filter criteria
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    data_source = relationship("DataSource", back_populates="companies")
    scrape_job = relationship("ScrapeJob", back_populates="companies")
    funding_rounds = relationship("FundingRound", back_populates="company", cascade="all, delete-orphan")


class FundingRound(Base):
    """Funding round history for scraped companies"""
    __tablename__ = "funding_round"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('scraped_company.id'), nullable=False, index=True)
    round_type = Column(String(50))  # Seed, Series A, Series B, etc.
    amount = Column(Float)  # Amount raised in USD
    amount_currency = Column(String(10), default="USD")
    date = Column(DateTime, index=True)
    lead_investors = Column(Text)  # Comma-separated investor names
    valuation = Column(Float)  # Post-money valuation
    valuation_currency = Column(String(10), default="USD")
    source_url = Column(String(500))  # Where this data came from
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    company = relationship("ScrapedCompany", back_populates="funding_rounds")


class DataSource(Base):
    """Track data sources for scraped companies"""
    __tablename__ = "data_source"
    id = Column(Integer, primary_key=True)
    source_name = Column(String(100), nullable=False, unique=True, index=True)  # 'yc', 'techcrunch', etc.
    source_type = Column(String(50))  # 'api', 'rss', 'scraper', 'dataset'
    base_url = Column(String(500))
    api_key_required = Column(Boolean, default=False)
    reliability_score = Column(Float, default=0.5)  # 0-1 confidence in data quality
    last_scraped = Column(DateTime(timezone=True))
    scrape_frequency = Column(String(50))  # 'daily', 'weekly', 'monthly', 'on_demand'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    companies = relationship("ScrapedCompany", back_populates="data_source")


class ScrapeJob(Base):
    """Track scraping jobs"""
    __tablename__ = "scrape_job"
    id = Column(Integer, primary_key=True)
    status = Column(String(50), nullable=False, index=True)  # 'pending', 'running', 'completed', 'failed'
    job_type = Column(String(50))  # 'scheduled', 'on_demand', 'full_refresh'
    source_name = Column(String(100))  # Which source(s) to scrape
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    companies_found = Column(Integer, default=0)
    companies_added = Column(Integer, default=0)  # New companies added
    companies_updated = Column(Integer, default=0)  # Existing companies updated
    errors = Column(Text)  # Error messages if any
    job_metadata = Column(JSON)  # Additional job metadata (avoid reserved 'metadata')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    companies = relationship("ScrapedCompany", back_populates="scrape_job")
