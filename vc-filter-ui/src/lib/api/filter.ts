/**
 * Filter API Service
 * Handles firm filtering using AI-powered hybrid approach
 */

import { apiClient } from './client';
import type { FirmData } from './upload';

// ============================================================================
// Types
// ============================================================================

export interface FilterRequest {
  criteria: string;
  firms: FirmData[];
  top_n?: number;
  use_hybrid?: boolean;
}

export interface FilteredFirm {
  id: string;
  rank: number;
  name: string;
  score: number;
  reason: string;
  industry?: string;
  stage?: string;
  revenue?: string;
  location?: string;
  description?: string;
  valuation?: string;
  key_investors?: string;
  vector_similarity?: number;
}

export interface FilterMetadata {
  total_processed: number;
  processing_time_ms: number;
  filter_method: 'hybrid' | 'llm' | 'fallback';
  cache_hit: boolean;
  top_n_requested: number;
  top_n_returned: number;
}

export interface FilterResponse {
  results: FilteredFirm[];
  metadata: FilterMetadata;
}

// ============================================================================
// API Functions
// ============================================================================

export const filterApi = {
  /**
   * Filter and rank firms based on investment criteria
   * Uses AI-powered hybrid filtering (vector search + LLM)
   */
  async filterFirms(
    criteria: string,
    firms: FirmData[],
    options?: {
      topN?: number;
      useHybrid?: boolean;
    }
  ): Promise<FilterResponse> {
    const request: FilterRequest = {
      criteria,
      firms,
      top_n: options?.topN ?? 10,
      use_hybrid: options?.useHybrid ?? true,
    };
    
    return apiClient.post<FilterResponse>('/filter', request);
  },
};

export default filterApi;
