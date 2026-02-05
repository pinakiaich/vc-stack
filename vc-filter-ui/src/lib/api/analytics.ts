/**
 * Analytics API Service
 * Handles filter queries, results logging, and analytics
 */

import { apiClient } from './client';
import type { FilterQueryCreate, FirmResult } from '../../types';

interface QueryResponse {
  id: number;
  message: string;
}

interface AnalyticsSummary {
  total_queries: number;
  avg_processing_time: number;
  cache_hit_rate: number;
  rag_usage_rate: number;
  filter_methods: Record<string, number>;
}

interface TopCompany {
  name: string;
  avg_score: number;
  appearances: number;
}

export const analyticsApi = {
  /**
   * Log a filter query
   */
  async logQuery(query: FilterQueryCreate): Promise<QueryResponse> {
    return apiClient.post<QueryResponse>('/analytics/queries', query);
  },
  
  /**
   * Log filter results for a query
   */
  async logResults(queryId: number, results: FirmResult[]): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/analytics/results', {
      query_id: queryId,
      results: results.map(r => ({
        name: r.name,
        score: r.score,
        reason: r.reason,
        vector_similarity: r.opportunityScore, // Map if available
      })),
    });
  },
  
  /**
   * Log user feedback on a result
   */
  async logFeedback(
    resultId: number, 
    action: 'selected' | 'rejected' | 're-ranked' | 'viewed',
    userNotes?: string,
    rating?: number
  ): Promise<{ id: number; message: string }> {
    return apiClient.post('/analytics/feedback', {
      result_id: resultId,
      action,
      user_notes: userNotes,
      rating,
    });
  },
  
  /**
   * Get query history
   */
  async getQueryHistory(params?: {
    userId?: string;
    limit?: number;
    days?: number;
  }): Promise<FilterQueryCreate[]> {
    return apiClient.get('/analytics/queries', {
      params: {
        user_id: params?.userId,
        limit: params?.limit,
        days: params?.days,
      },
    });
  },
  
  /**
   * Get analytics summary
   */
  async getSummary(days: number = 30): Promise<AnalyticsSummary> {
    return apiClient.get('/analytics/summary', { params: { days } });
  },
  
  /**
   * Get top companies
   */
  async getTopCompanies(limit: number = 10, days: number = 30): Promise<TopCompany[]> {
    return apiClient.get('/analytics/top-companies', { params: { limit, days } });
  },
};

export default analyticsApi;
