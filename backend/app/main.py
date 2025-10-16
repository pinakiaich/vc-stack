from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from .core.db import Base, engine, SessionLocal
from .models import Company, FilterResult

app = FastAPI(title="VC Stack API (MVP)")
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

