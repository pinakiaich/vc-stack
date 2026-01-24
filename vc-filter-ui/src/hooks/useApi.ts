/**
 * API Hooks
 * React hooks for API interactions
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient, dealsApi, researchApi, analyticsApi } from '../lib/api';
import { useAppStore, actions } from '../store/appStore';
import type { Deal, DealCreate, ResearchFinding, FirmResult } from '../types';

// ============================================================================
// Health Check Hook
// ============================================================================

export function useHealthCheck() {
  const { dispatch } = useAppStore();
  const [checking, setChecking] = useState(false);
  
  const checkHealth = useCallback(async () => {
    setChecking(true);
    try {
      await apiClient.healthCheck();
      dispatch(actions.setApiConnected(true));
      return true;
    } catch {
      dispatch(actions.setApiConnected(false));
      return false;
    } finally {
      setChecking(false);
    }
  }, [dispatch]);
  
  useEffect(() => {
    checkHealth();
    
    // Check health periodically
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);
  
  return { checking, checkHealth };
}

// ============================================================================
// Deals Hook
// ============================================================================

export function useDeals() {
  const { state, dispatch } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchDeals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const deals = await dealsApi.list();
      dispatch(actions.setDeals(deals));
      return deals;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch deals';
      setError(message);
      return [];
    } finally {
      setLoading(false);
    }
  }, [dispatch]);
  
  const createDeal = useCallback(async (deal: DealCreate): Promise<Deal | null> => {
    setLoading(true);
    setError(null);
    try {
      const newDeal = await dealsApi.create(deal);
      dispatch(actions.addDeal(newDeal));
      return newDeal;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create deal';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [dispatch]);
  
  const getDeal = useCallback(async (dealId: number): Promise<Deal | null> => {
    setLoading(true);
    setError(null);
    try {
      const deal = await dealsApi.getById(dealId);
      dispatch(actions.setSelectedDeal(deal));
      return deal;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch deal';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [dispatch]);
  
  return {
    deals: state.deals,
    selectedDeal: state.selectedDeal,
    loading,
    error,
    fetchDeals,
    createDeal,
    getDeal,
    setSelectedDeal: (deal: Deal | null) => dispatch(actions.setSelectedDeal(deal)),
  };
}

// ============================================================================
// Research Hook
// ============================================================================

export function useResearch(dealId?: number) {
  const [findings, setFindings] = useState<ResearchFinding[]>([]);
  const [findingsByCategory, setFindingsByCategory] = useState<Record<string, ResearchFinding[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchFindings = useCallback(async () => {
    if (!dealId) return [];
    
    setLoading(true);
    setError(null);
    try {
      const data = await researchApi.getFindings(dealId);
      setFindings(data);
      
      // Group by category
      const grouped = data.reduce((acc, finding) => {
        const category = finding.category || 'general';
        if (!acc[category]) acc[category] = [];
        acc[category].push(finding);
        return acc;
      }, {} as Record<string, ResearchFinding[]>);
      setFindingsByCategory(grouped);
      
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch research';
      setError(message);
      return [];
    } finally {
      setLoading(false);
    }
  }, [dealId]);
  
  const addFinding = useCallback(async (
    category: string,
    content: string,
    sourceType?: string,
    citation?: string
  ): Promise<ResearchFinding | null> => {
    if (!dealId) return null;
    
    setLoading(true);
    setError(null);
    try {
      const finding = await researchApi.createFinding(dealId, {
        category,
        content,
        source_type: sourceType,
        citation,
      });
      
      // Update local state
      setFindings(prev => [finding, ...prev]);
      setFindingsByCategory(prev => {
        const cat = category || 'general';
        return {
          ...prev,
          [cat]: [finding, ...(prev[cat] || [])],
        };
      });
      
      return finding;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to add finding';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [dealId]);
  
  useEffect(() => {
    if (dealId) {
      fetchFindings();
    }
  }, [dealId, fetchFindings]);
  
  return {
    findings,
    findingsByCategory,
    loading,
    error,
    fetchFindings,
    addFinding,
  };
}

// ============================================================================
// Analytics Hook
// ============================================================================

export function useAnalytics() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const logFilterQuery = useCallback(async (
    criteria: string,
    totalFirms: number,
    processingTimeMs: number,
    filterMethod: string,
    options?: { usedCache?: boolean; usedRag?: boolean; userId?: string }
  ) => {
    try {
      const response = await analyticsApi.logQuery({
        criteria,
        total_firms: totalFirms,
        processing_time_ms: processingTimeMs,
        filter_method: filterMethod,
        used_cache: options?.usedCache,
        used_rag: options?.usedRag,
        user_id: options?.userId,
      });
      return response.id;
    } catch (err) {
      console.error('Failed to log query:', err);
      return null;
    }
  }, []);
  
  const logFilterResults = useCallback(async (queryId: number, results: FirmResult[]) => {
    try {
      await analyticsApi.logResults(queryId, results);
      return true;
    } catch (err) {
      console.error('Failed to log results:', err);
      return false;
    }
  }, []);
  
  const logFeedback = useCallback(async (
    resultId: number,
    action: 'selected' | 'rejected' | 're-ranked' | 'viewed',
    userNotes?: string,
    rating?: number
  ) => {
    try {
      await analyticsApi.logFeedback(resultId, action, userNotes, rating);
      return true;
    } catch (err) {
      console.error('Failed to log feedback:', err);
      return false;
    }
  }, []);
  
  const getSummary = useCallback(async (days: number = 30) => {
    setLoading(true);
    setError(null);
    try {
      return await analyticsApi.getSummary(days);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch summary';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);
  
  return {
    loading,
    error,
    logFilterQuery,
    logFilterResults,
    logFeedback,
    getSummary,
  };
}
