/**
 * Research API Service
 * Handles research findings and company research
 */

import { apiClient } from './client';
import type { ResearchFinding, ResearchFindingCreate } from '../../types';

export const researchApi = {
  /**
   * Create a research finding for a deal
   */
  async createFinding(dealId: number, finding: Omit<ResearchFindingCreate, 'deal_id'>): Promise<ResearchFinding> {
    return apiClient.post<ResearchFinding>(`/v2/deals/${dealId}/research-findings`, {
      deal_id: dealId,
      ...finding,
    });
  },
  
  /**
   * Get all research findings for a deal
   */
  async getFindings(dealId: number): Promise<ResearchFinding[]> {
    return apiClient.get<ResearchFinding[]>(`/v2/deals/${dealId}/research-findings`);
  },
  
  /**
   * Get findings grouped by category
   */
  async getFindingsByCategory(dealId: number): Promise<Record<string, ResearchFinding[]>> {
    const findings = await this.getFindings(dealId);
    
    return findings.reduce((acc, finding) => {
      const category = finding.category || 'general';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(finding);
      return acc;
    }, {} as Record<string, ResearchFinding[]>);
  },
};

export default researchApi;
