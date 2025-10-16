from sqlalchemy import Column, Integer, String, Text, Float, DateTime
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

class FilterResult(Base):
    __tablename__ = "filter_result"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, nullable=False)
    heuristics = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
