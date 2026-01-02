"""
Analytics Service for tracking queries, results, and generating insights
"""
import logging
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.app.models import FilterQuery, FilterResult, UserFeedback, Company
from backend.app.core.db import SessionLocal


class AnalyticsService:
    """Service for analytics and query tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def log_filter_query(
        self,
        criteria: str,
        total_firms: int,
        processing_time_ms: int,
        filter_method: str,
        used_cache: bool = False,
        used_rag: bool = False,
        user_id: Optional[str] = None
    ) -> int:
        """
        Log a filter query to the database
        
        Returns:
            Query ID for linking results
        """
        db = SessionLocal()
        try:
            query = FilterQuery(
                user_id=user_id,
                criteria=criteria,
                total_firms_analyzed=total_firms,
                processing_time_ms=processing_time_ms,
                filter_method=filter_method,
                used_cache=used_cache,
                used_rag=used_rag
            )
            db.add(query)
            db.commit()
            db.refresh(query)
            return query.id
        except Exception as e:
            self.logger.error(f"Error logging filter query: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def log_filter_results(
        self,
        query_id: int,
        results: List[Dict],
        company_map: Optional[Dict[str, int]] = None
    ) -> None:
        """
        Log filter results to the database
        
        Args:
            query_id: Filter query ID
            results: List of result dictionaries with name, score, reason, etc.
            company_map: Optional mapping of company names to company IDs
        """
        db = SessionLocal()
        try:
            for rank, result in enumerate(results, 1):
                company_name = result.get('name', 'Unknown')
                company_id = None
                
                # Try to find or create company
                if company_map and company_name in company_map:
                    company_id = company_map[company_name]
                else:
                    # Try to find existing company by name
                    company = db.query(Company).filter(Company.name == company_name).first()
                    if company:
                        company_id = company.id
                    else:
                        # Create new company (minimal info)
                        company = Company(name=company_name)
                        db.add(company)
                        db.flush()
                        company_id = company.id
                
                filter_result = FilterResult(
                    query_id=query_id,
                    company_id=company_id,
                    company_name=company_name,
                    score=result.get('score', 0.0),
                    rank=rank,
                    reason=result.get('reason'),
                    vector_similarity=result.get('vector_similarity')
                )
                db.add(filter_result)
            
            db.commit()
        except Exception as e:
            self.logger.error(f"Error logging filter results: {e}")
            db.rollback()
        finally:
            db.close()
    
    def add_feedback(
        self,
        result_id: int,
        action: str,
        user_notes: Optional[str] = None,
        rating: Optional[int] = None
    ) -> None:
        """Add user feedback on a filter result"""
        db = SessionLocal()
        try:
            feedback = UserFeedback(
                result_id=result_id,
                action=action,
                user_notes=user_notes,
                rating=rating
            )
            db.add(feedback)
            db.commit()
        except Exception as e:
            self.logger.error(f"Error adding feedback: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_query_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
        days: Optional[int] = None
    ) -> List[Dict]:
        """Get query history with optional filters"""
        db = SessionLocal()
        try:
            query = db.query(FilterQuery)
            
            if user_id:
                query = query.filter(FilterQuery.user_id == user_id)
            
            if days:
                cutoff_date = datetime.now() - timedelta(days=days)
                query = query.filter(FilterQuery.created_at >= cutoff_date)
            
            queries = query.order_by(desc(FilterQuery.created_at)).limit(limit).all()
            
            return [
                {
                    'id': q.id,
                    'criteria': q.criteria,
                    'total_firms': q.total_firms_analyzed,
                    'processing_time_ms': q.processing_time_ms,
                    'filter_method': q.filter_method,
                    'used_cache': q.used_cache,
                    'used_rag': q.used_rag,
                    'created_at': q.created_at.isoformat() if q.created_at else None
                }
                for q in queries
            ]
        finally:
            db.close()
    
    def get_analytics_summary(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics summary for the last N days"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Total queries
            total_queries = db.query(FilterQuery).filter(
                FilterQuery.created_at >= cutoff_date
            ).count()
            
            # Average processing time
            avg_time = db.query(func.avg(FilterQuery.processing_time_ms)).filter(
                FilterQuery.created_at >= cutoff_date
            ).scalar() or 0
            
            # Cache hit rate
            queries_with_cache = db.query(FilterQuery).filter(
                FilterQuery.created_at >= cutoff_date,
                FilterQuery.used_cache == True
            ).count()
            cache_hit_rate = queries_with_cache / total_queries if total_queries > 0 else 0
            
            # RAG usage rate
            queries_with_rag = db.query(FilterQuery).filter(
                FilterQuery.created_at >= cutoff_date,
                FilterQuery.used_rag == True
            ).count()
            rag_usage_rate = queries_with_rag / total_queries if total_queries > 0 else 0
            
            # Filter method distribution
            method_counts = db.query(
                FilterQuery.filter_method,
                func.count(FilterQuery.id)
            ).filter(
                FilterQuery.created_at >= cutoff_date
            ).group_by(FilterQuery.filter_method).all()
            
            method_distribution = {method: count for method, count in method_counts}
            
            # Most common criteria patterns (top 5)
            common_criteria = db.query(
                FilterQuery.criteria,
                func.count(FilterQuery.id).label('count')
            ).filter(
                FilterQuery.created_at >= cutoff_date
            ).group_by(FilterQuery.criteria).order_by(
                desc('count')
            ).limit(5).all()
            
            return {
                'total_queries': total_queries,
                'avg_processing_time_ms': float(avg_time),
                'cache_hit_rate': cache_hit_rate,
                'rag_usage_rate': rag_usage_rate,
                'method_distribution': method_distribution,
                'common_criteria': [{'criteria': c, 'count': count} for c, count in common_criteria],
                'period_days': days
            }
        finally:
            db.close()
    
    def get_top_companies(
        self,
        limit: int = 10,
        days: int = 30
    ) -> List[Dict]:
        """Get top companies by average score"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            top_companies = db.query(
                FilterResult.company_name,
                func.avg(FilterResult.score).label('avg_score'),
                func.count(FilterResult.id).label('appearances')
            ).join(FilterQuery).filter(
                FilterQuery.created_at >= cutoff_date
            ).group_by(
                FilterResult.company_name
            ).order_by(
                desc('avg_score')
            ).limit(limit).all()
            
            return [
                {
                    'company_name': name,
                    'avg_score': float(avg_score),
                    'appearances': appearances
                }
                for name, avg_score, appearances in top_companies
            ]
        finally:
            db.close()
