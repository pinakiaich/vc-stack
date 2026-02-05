/**
 * Companies API Service
 * Handles company data operations
 */

import { apiClient } from './client';
import type { Company, CompanyCreate } from '../../types';

export const companiesApi = {
  /**
   * Create a new company
   */
  async create(company: CompanyCreate): Promise<Company> {
    return apiClient.post<Company>('/companies', company);
  },
  
  /**
   * Get all companies
   */
  async list(): Promise<Company[]> {
    return apiClient.get<Company[]>('/companies');
  },
};

export default companiesApi;
