from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import io
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy import func
from .core.db import Base, engine, SessionLocal
from .models import Company, FilterResult, FilterQuery, UserFeedback
from .models import Deal  # v2 models
from .schemas_v2 import DealCreate, DealRead, ResearchFindingCreate, ResearchFindingRead
from .models import ResearchFinding
from .models import ScrapedCompany, FundingRound, DataSource, ScrapeJob
from .scraper.service import ScraperService

# Configure logging for scraper debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Set scraper modules to INFO level for detailed output
logging.getLogger('app.scraper').setLevel(logging.INFO)
logging.getLogger('app.scraper.service').setLevel(logging.INFO)
logging.getLogger('app.scraper.validator').setLevel(logging.INFO)
logging.getLogger('app.scraper.sources').setLevel(logging.INFO)

app = FastAPI(title="VC Stack API")

# CORS configuration - MUST be first to handle preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# Request logging middleware (after CORS)
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = logging.getLogger(__name__)
        logger.info(f"{request.method} {request.url.path} - Origin: {request.headers.get('origin', 'none')}")
        try:
            response = await call_next(request)
            logger.info(f"{request.method} {request.url.path} - Status: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"{request.method} {request.url.path} - Error: {e}", exc_info=True)
            raise

app.add_middleware(LoggingMiddleware)

Base.metadata.create_all(bind=engine)


def _ensure_match_reasoning_column():
    """Add match_reasoning column to scraped_company if missing (SQLite migration)."""
    from sqlalchemy import text
    logger = logging.getLogger(__name__)
    if "sqlite" not in str(engine.url):
        return
    try:
        with engine.connect() as conn:
            r = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='scraped_company'"))
            if not r.fetchone():
                return  # Table not created yet; create_all will create it with all columns
            r = conn.execute(text("PRAGMA table_info(scraped_company)"))
            columns = [row[1] for row in r.fetchall()]
        if "match_reasoning" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE scraped_company ADD COLUMN match_reasoning TEXT"))
            logger.info("Added scraped_company.match_reasoning column")
    except Exception as e:
        logger.warning("Migration check for match_reasoning: %s", e)


_ensure_match_reasoning_column()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/detailed")
def health_detailed(db=Depends(get_db)):
    """Detailed health check that tests database connection"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        company_count = db.query(ScrapedCompany).count()
        return {
            "status": "ok",
            "database": "connected",
            "companies_in_db": company_count
        }
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }


# ============================================================================
# File Upload & Parsing Endpoints
# ============================================================================

class ColumnInfo(BaseModel):
    name: str
    dtype: str
    non_null_count: int
    sample_values: List[str]

class ParsedFileResponse(BaseModel):
    filename: str
    total_rows: int
    total_columns: int
    columns: List[ColumnInfo]
    detected_name_column: Optional[str]
    detected_columns: Dict[str, Optional[str]]  # Maps standard fields to detected columns
    preview_rows: List[Dict[str, Any]]
    warnings: List[str]

def detect_column_mapping(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Auto-detect which columns map to standard fields"""
    mapping = {
        'name': None,
        'description': None,
        'industry': None,
        'stage': None,
        'revenue': None,
        'location': None,
        'valuation': None,
        'key_investors': None,
        'opportunity_score': None,
        'exit_probability_score': None,
    }
    
    # Column name patterns for each field (ordered by priority - exact matches first)
    # For 'name', we prioritize more specific patterns to avoid false matches
    patterns = {
        'name': [
            'company name', 'firm name', 'company', 'companies', 'firm', 'portfolio company',
            'target company', 'startup name', 'startup', 'name'  # 'name' last as it's generic
        ],
        'description': ['description', 'company description', 'about', 'summary', 'overview', 'business description'],
        'industry': ['primary industry', 'industry', 'sector', 'vertical', 'market', 'industry sector'],
        'stage': ['funding stage', 'investment stage', 'stage', 'round', 'series', 'deal type', 'financing deal type', 'first financing deal type'],
        'revenue': ['revenue', 'arr', 'annual revenue', 'total revenue', 'sales', 'mrr', 'annual recurring revenue'],
        'location': ['headquarters', 'hq', 'location', 'city', 'country', 'region', 'hq location', 'company location'],
        'valuation': [
            'valuation', 'last valuation', 'post-money valuation', 'post money valuation', 
            'pre-money valuation', 'pre money valuation', 'company valuation', 'latest valuation',
            'valuation at last round', 'last round valuation'
        ],
        'key_investors': [
            'key investors', 'investors', 'lead investor', 'lead investors', 'notable investors',
            'top investors', 'major investors', 'investor names', 'vcs', 'venture investors',
            'backers', 'funded by'
        ],
        'opportunity_score': ['opportunity score', 'opportunity', 'opp score'],
        'exit_probability_score': ['exit probability score', 'exit probability', 'exit prob', 'exit score'],
    }
    
    df_columns_lower = {col.lower().strip(): col for col in df.columns}
    
    # Track which columns have been assigned to avoid duplicates
    assigned_columns = set()
    
    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            pattern_lower = pattern.lower()
            
            # Priority 1: Exact match
            if pattern_lower in df_columns_lower:
                candidate = df_columns_lower[pattern_lower]
                if candidate not in assigned_columns:
                    mapping[field] = candidate
                    assigned_columns.add(candidate)
                    break
            
            # Priority 2: Column starts with pattern (e.g., "Company Name (Legal)")
            if not mapping[field]:
                for col_lower, col_original in df_columns_lower.items():
                    if col_lower.startswith(pattern_lower) and col_original not in assigned_columns:
                        mapping[field] = col_original
                        assigned_columns.add(col_original)
                        break
            
            # Priority 3: Pattern is contained in column name
            if not mapping[field]:
                for col_lower, col_original in df_columns_lower.items():
                    if pattern_lower in col_lower and col_original not in assigned_columns:
                        # Avoid matching "name" in columns like "Last Name", "Founder Name"
                        if field == 'name':
                            # Skip if it looks like a person's name column
                            skip_keywords = ['first', 'last', 'founder', 'ceo', 'contact', 'person', 'owner']
                            if any(skip in col_lower for skip in skip_keywords):
                                continue
                        mapping[field] = col_original
                        assigned_columns.add(col_original)
                        break
            
            if mapping[field]:
                break
    
    return mapping

def clean_dataframe(df: pd.DataFrame, skip_rows: int = 0) -> tuple[pd.DataFrame, List[str]]:
    """Clean the dataframe and return warnings"""
    warnings = []
    
    # Skip metadata rows
    if skip_rows > 0:
        df = df.iloc[skip_rows:].reset_index(drop=True)
        warnings.append(f"Skipped {skip_rows} metadata rows")
    
    # Auto-detect header row (look for rows that seem like metadata)
    if len(df) > 0:
        first_row = df.iloc[0]
        # Check if first row looks like metadata (e.g., dates, "Downloaded on", etc.)
        metadata_keywords = ['downloaded', 'created', 'exported', 'generated', 'report']
        first_cell = str(first_row.iloc[0] if len(first_row) > 0 else '').lower()
        if any(keyword in first_cell for keyword in metadata_keywords):
            df = df.iloc[1:].reset_index(drop=True)
            warnings.append("Auto-skipped metadata row detected at top")
    
    # Remove completely empty rows
    rows_before = len(df)
    df = df.dropna(how='all')
    rows_removed = rows_before - len(df)
    if rows_removed > 0:
        warnings.append(f"Removed {rows_removed} empty rows")
    
    # Convert all columns to string for consistency (except numeric)
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('').astype(str)
    
    return df, warnings

@app.post("/upload/parse", response_model=ParsedFileResponse)
async def parse_uploaded_file(
    file: UploadFile = File(...),
    skip_rows: int = 0,
    name_column: Optional[str] = None
):
    """
    Parse an uploaded Excel file and return structured data.
    
    - Accepts .xlsx and .xls files
    - Auto-detects column mappings
    - Returns preview rows and column info
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = file.filename.lower().split('.')[-1]
    if file_ext not in ['xlsx', 'xls']:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}. Use .xlsx or .xls")
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse Excel file
        df = pd.read_excel(io.BytesIO(content), engine='openpyxl' if file_ext == 'xlsx' else 'xlrd')
        
        # Clean the dataframe
        df, warnings = clean_dataframe(df, skip_rows)
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="File contains no data after cleaning")
        
        # Detect column mappings
        detected_columns = detect_column_mapping(df)
        
        # Override name column if specified
        if name_column and name_column in df.columns:
            detected_columns['name'] = name_column
        
        # Build column info
        columns_info = []
        for col in df.columns:
            non_null = df[col].notna().sum()
            # Get sample values (first 3 non-empty values)
            sample_vals = df[col].dropna().head(3).astype(str).tolist()
            columns_info.append(ColumnInfo(
                name=str(col),
                dtype=str(df[col].dtype),
                non_null_count=int(non_null),
                sample_values=sample_vals
            ))
        
        # Get preview rows (first 10) - convert all values to native Python types
        preview_df = df.head(10).fillna('')
        preview_rows = []
        for _, row in preview_df.iterrows():
            preview_rows.append({str(k): str(v) if v != '' else '' for k, v in row.items()})
        
        # Add warning if name column not detected
        if not detected_columns.get('name'):
            warnings.append("Could not auto-detect company name column. Please specify manually.")
        
        return ParsedFileResponse(
            filename=file.filename,
            total_rows=int(len(df)),
            total_columns=int(len(df.columns)),
            columns=columns_info,
            detected_name_column=detected_columns.get('name'),
            detected_columns=detected_columns,
            preview_rows=preview_rows,
            warnings=warnings
        )
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="File is empty")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing file: {str(e)}")


class FirmData(BaseModel):
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    stage: Optional[str] = None
    revenue: Optional[str] = None
    location: Optional[str] = None
    valuation: Optional[str] = None
    key_investors: Optional[str] = None
    raw_data: Dict[str, Any] = {}

class ExtractedFirmsResponse(BaseModel):
    filename: str
    total_firms: int
    firms: List[FirmData]
    column_mapping: Dict[str, Optional[str]]
    warnings: List[str]

@app.post("/upload/extract-firms", response_model=ExtractedFirmsResponse)
async def extract_firms_from_file(
    file: UploadFile = File(...),
    skip_rows: int = 0,
    name_column: Optional[str] = None,
    industry_column: Optional[str] = None,
    stage_column: Optional[str] = None,
    description_column: Optional[str] = None,
    valuation_column: Optional[str] = None,
    key_investors_column: Optional[str] = None,
    revenue_column: Optional[str] = None,
    location_column: Optional[str] = None,
):
    """
    Extract firm data from an uploaded Excel file.
    
    - Returns structured firm data ready for filtering
    - Allows manual column mapping overrides for all fields
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = file.filename.lower().split('.')[-1]
    if file_ext not in ['xlsx', 'xls']:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")
    
    try:
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content), engine='openpyxl' if file_ext == 'xlsx' else 'xlrd')
        df, warnings = clean_dataframe(df, skip_rows)
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="No data found in file")
        
        # Detect column mappings
        detected = detect_column_mapping(df)
        
        # Apply manual overrides for all fields
        if name_column and name_column in df.columns:
            detected['name'] = name_column
        if industry_column and industry_column in df.columns:
            detected['industry'] = industry_column
        if stage_column and stage_column in df.columns:
            detected['stage'] = stage_column
        if description_column and description_column in df.columns:
            detected['description'] = description_column
        if valuation_column and valuation_column in df.columns:
            detected['valuation'] = valuation_column
        if key_investors_column and key_investors_column in df.columns:
            detected['key_investors'] = key_investors_column
        if revenue_column and revenue_column in df.columns:
            detected['revenue'] = revenue_column
        if location_column and location_column in df.columns:
            detected['location'] = location_column
        
        # Validate name column exists
        if not detected.get('name'):
            raise HTTPException(
                status_code=400, 
                detail="Could not detect company name column. Please specify name_column parameter."
            )
        
        # Extract firms
        firms = []
        name_col = detected['name']
        
        def get_field_value(row, field_name):
            """Safely get a field value as string"""
            col = detected.get(field_name)
            if not col or col not in row:
                return None
            val = row.get(col, '')
            if pd.isna(val):
                return None
            return str(val).strip() or None
        
        for idx, row in df.iterrows():
            name = str(row.get(name_col, '')).strip()
            if not name or name.lower() in ['nan', 'none', '']:
                continue
            
            # Convert raw_data to native Python types
            raw_data = {}
            for k, v in row.to_dict().items():
                if pd.isna(v):
                    raw_data[str(k)] = ''
                else:
                    raw_data[str(k)] = str(v)
            
            firm = FirmData(
                name=name,
                description=get_field_value(row, 'description'),
                industry=get_field_value(row, 'industry'),
                stage=get_field_value(row, 'stage'),
                revenue=get_field_value(row, 'revenue'),
                location=get_field_value(row, 'location'),
                valuation=get_field_value(row, 'valuation'),
                key_investors=get_field_value(row, 'key_investors'),
                raw_data=raw_data
            )
            firms.append(firm)
        
        if len(firms) == 0:
            warnings.append("No valid firms found. Check that the name column contains data.")
        
        return ExtractedFirmsResponse(
            filename=file.filename,
            total_firms=int(len(firms)),
            firms=firms,
            column_mapping=detected,
            warnings=warnings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting firms: {str(e)}")


# ============================================================================
# Filter API Endpoint
# ============================================================================

class FilterRequest(BaseModel):
    """Request body for filter endpoint"""
    criteria: str
    firms: List[FirmData]
    top_n: int = 10
    use_hybrid: bool = True  # Use hybrid filter (vector + LLM) by default

class FilteredFirm(BaseModel):
    """Individual filtered firm result"""
    id: str
    rank: int
    name: str
    score: float
    reason: str
    industry: Optional[str] = None
    stage: Optional[str] = None
    revenue: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    valuation: Optional[str] = None
    key_investors: Optional[str] = None
    vector_similarity: Optional[float] = None

class FilterMetadata(BaseModel):
    """Metadata about the filter operation"""
    total_processed: int
    processing_time_ms: int
    filter_method: str  # 'hybrid', 'llm', 'fallback'
    cache_hit: bool
    top_n_requested: int
    top_n_returned: int

class FilterResponse(BaseModel):
    """Response from filter endpoint"""
    results: List[FilteredFirm]
    metadata: FilterMetadata


# ============================================================================
# VC Analyst Agent – Research thesis → suggested attributes + heuristics
# ============================================================================

class ThesisSuggestRequest(BaseModel):
    """Request for VC Analyst thesis suggestions"""
    thesis: str
    api_key: Optional[str] = None  # Optional; otherwise uses OPENAI_API_KEY


class ThesisSuggestResponse(BaseModel):
    """VC Analyst suggestions from research thesis"""
    ok: bool
    suggested_attributes: Optional[Dict[str, Any]] = None
    heuristics: Optional[str] = None
    error: Optional[str] = None


@app.post("/research/thesis/suggest", response_model=ThesisSuggestResponse)
def thesis_suggest(request: ThesisSuggestRequest):
    """
    VC Analyst Agent: interpret research thesis → suggested attributes + heuristics.

    Use these for structured filters (scraper) and qualitative criteria (AI filter).
    """
    from .analyst.vc_analyst_agent import suggest_from_thesis

    result = suggest_from_thesis(request.thesis, api_key=request.api_key)
    if result.get("ok"):
        return ThesisSuggestResponse(
            ok=True,
            suggested_attributes=result.get("suggested_attributes"),
            heuristics=result.get("heuristics"),
        )
    return ThesisSuggestResponse(ok=False, error=result.get("error", "Unknown error"))


@app.post("/filter", response_model=FilterResponse)
async def filter_firms_endpoint(request: FilterRequest):
    """
    Filter and rank firms based on investment criteria.
    
    - Uses AI-powered hybrid filtering (vector search + LLM analysis)
    - Returns ranked firms with scores and explanations
    """
    import time
    import sys
    from pathlib import Path
    
    start_time = time.time()
    
    # Add parent directory to path for imports
    backend_parent = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(backend_parent))
    
    try:
        from config import Config
        from ai_filter import AIFilter
        
        # Initialize config and filter
        config = Config()
        ai_filter = AIFilter(config, use_hybrid_filter=request.use_hybrid)
        
        # Convert FirmData to dict format expected by AIFilter
        firms_data = []
        firm_lookup = {}  # Map name to original FirmData for enriching results
        
        for i, firm in enumerate(request.firms):
            firm_dict = {
                'name': firm.name,
                'description': firm.description or '',
                'industry': firm.industry or '',
                'stage': firm.stage or '',
                'revenue': firm.revenue or '',
                'location': firm.location or '',
            }
            # Add raw_data fields if present
            if firm.raw_data:
                for key, value in firm.raw_data.items():
                    if key not in firm_dict:
                        firm_dict[key] = str(value) if value else ''
            
            firms_data.append(firm_dict)
            firm_lookup[firm.name] = firm
        
        # Convert to DataFrame for AIFilter
        df = pd.DataFrame(firms_data)
        
        # Run filter
        filter_results = ai_filter.filter_firms(df, request.criteria, top_n=request.top_n)
        
        # Determine filter method used
        filter_method = 'hybrid' if ai_filter.use_hybrid else 'llm'
        if not filter_results or (len(filter_results) > 0 and 'vector_similarity' not in filter_results[0]):
            filter_method = 'fallback'
        
        # Format results
        results = []
        for rank, result in enumerate(filter_results, 1):
            firm_name = result.get('name', 'Unknown')
            original_firm = firm_lookup.get(firm_name)
            
            results.append(FilteredFirm(
                id=str(rank),
                rank=rank,
                name=firm_name,
                score=float(result.get('score', 0)),
                reason=str(result.get('reason', '')),
                industry=original_firm.industry if original_firm else None,
                stage=original_firm.stage if original_firm else None,
                revenue=original_firm.revenue if original_firm else None,
                location=original_firm.location if original_firm else None,
                description=original_firm.description if original_firm else None,
                valuation=original_firm.valuation if original_firm else None,
                key_investors=original_firm.key_investors if original_firm else None,
                vector_similarity=float(result.get('vector_similarity', 0)) if result.get('vector_similarity') else None,
            ))
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Check if cache was hit (indicated by fast response time < 1 second for hybrid)
        cache_hit = processing_time_ms < 1000 and len(request.firms) > 10
        
        return FilterResponse(
            results=results,
            metadata=FilterMetadata(
                total_processed=len(request.firms),
                processing_time_ms=processing_time_ms,
                filter_method=filter_method,
                cache_hit=cache_hit,
                top_n_requested=request.top_n,
                top_n_returned=len(results),
            )
        )
        
    except ImportError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Filter dependencies not available: {str(e)}. Make sure ai_filter.py and dependencies are installed."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filter error: {str(e)}")


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


@app.post("/v2/deals/{deal_id}/research-findings", response_model=ResearchFindingRead)
def create_research_finding(deal_id: int, finding: ResearchFindingCreate, db=Depends(get_db)):
    """Create a research finding for a deal"""
    # Verify deal exists
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    # Create research finding
    finding_data = finding.dict()
    finding_data['deal_id'] = deal_id
    db_finding = ResearchFinding(**finding_data)
    db.add(db_finding)
    db.commit()
    db.refresh(db_finding)
    return db_finding


@app.get("/v2/deals/{deal_id}/research-findings", response_model=List[ResearchFindingRead])
def get_research_findings(deal_id: int, db=Depends(get_db)):
    """Get all research findings for a deal"""
    # Verify deal exists
    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    
    findings = db.query(ResearchFinding).filter(ResearchFinding.deal_id == deal_id).order_by(ResearchFinding.created_at.desc()).all()
    return findings


# ============================================================================
# Company Research Agent Endpoints
# ============================================================================

class ScrapedCompanyRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    industry: Optional[str]
    stage: Optional[str]
    valuation: Optional[float]
    key_investors: Optional[str]
    location: Optional[str]
    website: Optional[str]
    source_name: Optional[str] = None  # Source from data_source relationship
    match_reasoning: Optional[str] = None  # Why this company matched filters
    created_at: str
    
    class Config:
        from_attributes = True

class ScrapeJobRead(BaseModel):
    id: int
    status: str
    job_type: str
    source_name: str
    started_at: Optional[str]
    completed_at: Optional[str]
    companies_found: int
    companies_added: int
    companies_updated: int
    errors: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_scrape_job(cls, job: ScrapeJob):
        """Convert ScrapeJob model to ScrapeJobRead with proper datetime serialization"""
        return cls(
            id=job.id,
            status=job.status,
            job_type=job.job_type,
            source_name=job.source_name,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            companies_found=job.companies_found,
            companies_added=job.companies_added,
            companies_updated=job.companies_updated,
            errors=job.errors,
            created_at=job.created_at.isoformat() if job.created_at else '',
        )

class ScrapeRequest(BaseModel):
    source_names: Optional[List[str]] = None
    job_type: str = "on_demand"
    limit: Optional[int] = None  # Limit number of companies to process (for testing)

@app.get("/research/companies", response_model=List[ScrapedCompanyRead])
def list_scraped_companies(
    db=Depends(get_db),
    stage: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """List scraped companies with optional filters"""
    logger = logging.getLogger(__name__)
    logger.info(f"GET /research/companies called - stage={stage}, industry={industry}, limit={limit}")
    
    try:
        query = db.query(ScrapedCompany).filter(ScrapedCompany.is_validated == True)
        
        if stage:
            query = query.filter(ScrapedCompany.stage == stage)
        if industry:
            query = query.filter(ScrapedCompany.industry.ilike(f"%{industry}%"))
        
        companies = query.order_by(ScrapedCompany.created_at.desc()).offset(offset).limit(limit).all()
        logger.info(f"Returning {len(companies)} companies")
        # Return empty list if no companies (don't error)
        if not companies:
            logger.info("No companies found in database - returning empty list")
        
        # Convert datetime objects to ISO format strings and include source
        result = []
        for company in companies:
            # Get source name from relationship
            source_name = company.data_source.source_name if company.data_source else None
            result.append(ScrapedCompanyRead(
                id=company.id,
                name=company.name,
                description=company.description,
                industry=company.industry,
                stage=company.stage,
                valuation=company.valuation,
                key_investors=company.key_investors,
                location=company.location,
                website=company.website,
                source_name=source_name,
                match_reasoning=company.match_reasoning,
                created_at=company.created_at.isoformat() if company.created_at else '',
            ))
        return result
    except Exception as e:
        logger.error(f"Error listing companies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching companies: {str(e)}")

@app.get("/research/companies/{company_id}", response_model=ScrapedCompanyRead)
def get_scraped_company(company_id: int, db=Depends(get_db)):
    """Get a single scraped company"""
    company = db.query(ScrapedCompany).filter(ScrapedCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    # Convert datetime to ISO format string and include source
    source_name = company.data_source.source_name if company.data_source else None
    return ScrapedCompanyRead(
        id=company.id,
        name=company.name,
        description=company.description,
        industry=company.industry,
        stage=company.stage,
        valuation=company.valuation,
        key_investors=company.key_investors,
        location=company.location,
        website=company.website,
        source_name=source_name,
        match_reasoning=company.match_reasoning,
        created_at=company.created_at.isoformat() if company.created_at else '',
    )

@app.post("/research/scrape", response_model=ScrapeJobRead)
def trigger_scrape(request: ScrapeRequest, db=Depends(get_db)):
    """
    Trigger an on-demand scrape
    
    IMPORTANT: This endpoint should ONLY be called when the user explicitly clicks
    the "Run Scraper" button. It should NEVER be called automatically.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"SCRAPE ENDPOINT CALLED - source_names={request.source_names}, job_type={request.job_type}, limit={request.limit}")
    logger.info("This should only happen when user clicks 'Run Scraper' button")
    
    service = ScraperService(db)
    job = service.run_scrape(request.source_names, request.job_type, limit=request.limit)
    
    logger.info(f"Scrape job {job.id} created with status: {job.status}")
    # Convert datetime objects to ISO format strings
    return ScrapeJobRead.from_scrape_job(job)

@app.get("/research/scrape/status", response_model=List[ScrapeJobRead])
def get_scrape_status(db=Depends(get_db), limit: int = 10):
    """Get recent scrape job status"""
    jobs = db.query(ScrapeJob).order_by(ScrapeJob.created_at.desc()).limit(limit).all()
    # Convert datetime objects to ISO format strings
    return [ScrapeJobRead.from_scrape_job(job) for job in jobs]

@app.get("/research/export")
def export_companies_to_excel(
    db=Depends(get_db),
    stage: Optional[str] = None,
    industry: Optional[str] = None,
):
    """Export scraped companies to Excel"""
    from fastapi.responses import StreamingResponse
    
    query = db.query(ScrapedCompany).filter(ScrapedCompany.is_validated == True)
    
    if stage:
        query = query.filter(ScrapedCompany.stage == stage)
    if industry:
        query = query.filter(ScrapedCompany.industry.ilike(f"%{industry}%"))
    
    companies = query.all()
    
    # Convert to DataFrame
    data = []
    for company in companies:
        data.append({
            "Company": company.name,
            "Description": company.description or "",
            "Industry": company.industry or "",
            "Stage": company.stage or "",
            "Valuation": company.valuation or "",
            "Key Investors": company.key_investors or "",
            "Location": company.location or "",
            "Website": company.website or "",
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Companies')
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=scraped_companies.xlsx"}
    )

@app.get("/research/stats")
def get_research_stats(db=Depends(get_db)):
    """Get dashboard statistics"""
    total = db.query(ScrapedCompany).filter(ScrapedCompany.is_validated == True).count()
    
    # By stage
    stage_counts = {}
    stages = db.query(ScrapedCompany.stage, func.count(ScrapedCompany.id)).filter(
        ScrapedCompany.is_validated == True,
        ScrapedCompany.stage.isnot(None)
    ).group_by(ScrapedCompany.stage).all()
    stage_counts = {stage: count for stage, count in stages}
    
    # By source
    source_counts = {}
    sources = db.query(DataSource.source_name, func.count(ScrapedCompany.id)).join(
        ScrapedCompany
    ).filter(ScrapedCompany.is_validated == True).group_by(DataSource.source_name).all()
    source_counts = {source: count for source, count in sources}
    
    # Valuation ranges
    valuation_ranges = {
        "100M-200M": db.query(ScrapedCompany).filter(
            ScrapedCompany.is_validated == True,
            ScrapedCompany.valuation >= 100_000_000,
            ScrapedCompany.valuation < 200_000_000
        ).count(),
        "200M-300M": db.query(ScrapedCompany).filter(
            ScrapedCompany.is_validated == True,
            ScrapedCompany.valuation >= 200_000_000,
            ScrapedCompany.valuation < 300_000_000
        ).count(),
        "300M-400M": db.query(ScrapedCompany).filter(
            ScrapedCompany.is_validated == True,
            ScrapedCompany.valuation >= 300_000_000,
            ScrapedCompany.valuation < 400_000_000
        ).count(),
        "400M-500M": db.query(ScrapedCompany).filter(
            ScrapedCompany.is_validated == True,
            ScrapedCompany.valuation >= 400_000_000,
            ScrapedCompany.valuation <= 500_000_000
        ).count(),
    }
    
    return {
        "total_companies": total,
        "by_stage": stage_counts,
        "by_source": source_counts,
        "by_valuation_range": valuation_ranges,
    }

