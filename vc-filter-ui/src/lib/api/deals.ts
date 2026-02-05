/**
 * Deals API Service
 * Handles all deal-related API calls
 */

import { apiClient } from './client';
import type { Deal, DealCreate } from '../../types';

export const dealsApi = {
  /**
   * Create a new deal
   */
  async create(deal: DealCreate): Promise<Deal> {
    return apiClient.post<Deal>('/v2/deals', deal);
  },
  
  /**
   * Get all deals
   */
  async list(limit: number = 100): Promise<Deal[]> {
    return apiClient.get<Deal[]>('/v2/deals', { params: { limit } });
  },
  
  /**
   * Get a specific deal by ID
   */
  async getById(dealId: number): Promise<Deal> {
    return apiClient.get<Deal>(`/v2/deals/${dealId}`);
  },
};

export default dealsApi;
