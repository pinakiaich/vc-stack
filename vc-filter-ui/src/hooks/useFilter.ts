/**
 * Filter Hook
 * Handles firm filtering using AI-powered hybrid approach
 */

import { useState, useCallback } from 'react';
import { filterApi, type FilterResponse, type FirmData } from '../lib/api';
import { useAppStore, actions } from '../store/appStore';

interface UseFilterReturn {
  // State
  filterResponse: FilterResponse | null;
  isFiltering: boolean;
  error: string | null;
  
  // Actions
  filterFirms: (criteria: string, firms: FirmData[], topN?: number) => Promise<FilterResponse | null>;
  clearResults: () => void;
}

export function useFilter(): UseFilterReturn {
  const { dispatch } = useAppStore();
  
  const [filterResponse, setFilterResponse] = useState<FilterResponse | null>(null);
  const [isFiltering, setIsFiltering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  /**
   * Filter firms using AI-powered hybrid approach
   */
  const filterFirms = useCallback(async (
    criteria: string,
    firms: FirmData[],
    topN: number = 10
  ): Promise<FilterResponse | null> => {
    setIsFiltering(true);
    setError(null);
    dispatch(actions.setIsFiltering(true));
    dispatch(actions.setError(null));
    
    try {
      const response = await filterApi.filterFirms(criteria, firms, { topN });
      setFilterResponse(response);
      
      // Update app store with results
      // Map FilteredFirm to FirmResult format expected by store
      const firmResults = response.results.map(firm => ({
        id: firm.id,
        rank: firm.rank,
        name: firm.name,
        score: firm.score,
        reason: firm.reason,
        industry: firm.industry || 'Unknown',
        stage: firm.stage || 'Unknown',
        revenue: firm.revenue,
        location: firm.location,
        description: firm.description,
        valuation: firm.valuation,
        keyInvestors: firm.key_investors,
      }));
      
      dispatch(actions.setFilterResults({
        results: firmResults,
        metadata: {
          totalProcessed: response.metadata.total_processed,
          processingTimeMs: response.metadata.processing_time_ms,
          cacheHitRate: response.metadata.cache_hit ? 1 : 0,
          filterMethod: response.metadata.filter_method,
        },
      }));
      
      return response;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Filter failed';
      setError(message);
      dispatch(actions.setError(message));
      dispatch(actions.setIsFiltering(false));
      return null;
    } finally {
      setIsFiltering(false);
      dispatch(actions.setIsFiltering(false));
    }
  }, [dispatch]);
  
  /**
   * Clear filter results
   */
  const clearResults = useCallback(() => {
    setFilterResponse(null);
    setError(null);
    dispatch(actions.clearFilterResults());
  }, [dispatch]);
  
  return {
    filterResponse,
    isFiltering,
    error,
    filterFirms,
    clearResults,
  };
}

export default useFilter;
