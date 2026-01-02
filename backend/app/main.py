from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .core.db import Base, engine, SessionLocal
from .models import Company, FilterResult, FilterQuery, UserFeedback
from .models import Deal  # v2 models
from .schemas_v2 import DealCreate, DealRead

app = FastAPI(title="VC Stack API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

class CompanyIn(BaseModel):
    name: str
    description: Optional[str] = None
    stage: Optional[str] = None
    revenue: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None

class CompanyOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    stage: Optional[str]
    revenue: Optional[str]
    industry: Optional[str]
    location: Optional[str]

class FilterResultIn(BaseModel):
    company_id: int
    heuristics: str
    score: float
    reason: Optional[str] = None

@app.post("/companies", response_model=CompanyOut)
def create_company(item: CompanyIn, db=Depends(get_db)):
    c = Company(**item.dict())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@app.get("/companies", response_model=List[CompanyOut])
def list_companies(db=Depends(get_db)):
    return db.query(Company).limit(100).all()

@app.post("/filter-results")
def save_filter_result(item: FilterResultIn, db=Depends(get_db)):
    result = FilterResult(**item.dict())
    db.add(result)
    db.commit()
    db.refresh(result)
    return {"id": result.id, "message": "Filter result saved"}

# Analytics endpoints
class FilterQueryIn(BaseModel):
    criteria: str
    total_firms: int
    processing_time_ms: int
    filter_method: str
    used_cache: bool = False
    used_rag: bool = False
    user_id: Optional[str] = None

class FilterResultsIn(BaseModel):
    query_id: int
    results: List[Dict[str, Any]]

class FeedbackIn(BaseModel):
    result_id: int
    action: str
    user_notes: Optional[str] = None
    rating: Optional[int] = None

@app.post("/analytics/queries")
def create_filter_query(item: FilterQueryIn, db=Depends(get_db)):
    """Create a new filter query record"""
    from .models import FilterQuery
    query = FilterQuery(**item.dict())
    db.add(query)
    db.commit()
    db.refresh(query)
    return {"id": query.id, "message": "Query logged"}

@app.post("/analytics/results")
def create_filter_results(item: FilterResultsIn, db=Depends(get_db)):
    """Log filter results for a query"""
    from .models import FilterResult, Company
    
    # Verify query exists
    query = db.query(FilterQuery).filter(FilterQuery.id == item.query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    for rank, result in enumerate(item.results, 1):
        company_name = result.get('name', 'Unknown')
        
        # Find or create company
        company = db.query(Company).filter(Company.name == company_name).first()
        if not company:
            company = Company(name=company_name)
            db.add(company)
            db.flush()
        
        filter_result = FilterResult(
            query_id=item.query_id,
            company_id=company.id,
            company_name=company_name,
            score=result.get('score', 0.0),
            rank=rank,
            reason=result.get('reason'),
            vector_similarity=result.get('vector_similarity')
        )
        db.add(filter_result)
    
    db.commit()
    return {"message": f"{len(item.results)} results logged"}

@app.post("/analytics/feedback")
def add_feedback(item: FeedbackIn, db=Depends(get_db)):
    """Add user feedback on a filter result"""
    feedback = UserFeedback(**item.dict())
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {"id": feedback.id, "message": "Feedback saved"}

@app.get("/analytics/queries")
def get_query_history(user_id: Optional[str] = None, limit: int = 100, days: Optional[int] = None):
    """Get query history"""
    import sys
    from pathlib import Path
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from analytics_service import AnalyticsService
    service = AnalyticsService()
    return service.get_query_history(user_id=user_id, limit=limit, days=days)

@app.get("/analytics/summary")
def get_analytics_summary(days: int = 30):
    """Get analytics summary"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from analytics_service import AnalyticsService
    service = AnalyticsService()
    return service.get_analytics_summary(days=days)

@app.get("/analytics/top-companies")
def get_top_companies(limit: int = 10, days: int = 30):
    """Get top companies by average score"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from analytics_service import AnalyticsService
    service = AnalyticsService()
    return service.get_top_companies(limit=limit, days=days)


# ============================================================================
# VC-Stack v2 Endpoints: Deal Workspace
# ============================================================================

@app.post("/v2/deals", response_model=DealRead)
def create_deal(deal: DealCreate, db=Depends(get_db)):
    """Create a new deal"""
    db_deal = Deal(**deal.dict())
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    return db_deal


@app.get("/v2/deals", response_model=List[DealRead])
def list_deals(db=Depends(get_db), limit: int = 100):
    """List all deals"""
    deals = db.query(Deal).order_by(Deal.created_at.desc()).limit(limit).all()
    return deals


@app.get("/v2/deals/{deal_id}", response_model=DealRead)
def get_deal(deal_id: int, db=Depends(get_db)):
    """Get a specific deal by ID"""
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

