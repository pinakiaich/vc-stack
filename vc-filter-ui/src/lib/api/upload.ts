/**
 * File Upload API Service
 * Handles Excel file parsing and firm extraction
 */

import { apiClient } from './client';

// ============================================================================
// Types
// ============================================================================

export interface ColumnInfo {
  name: string;
  dtype: string;
  non_null_count: number;
  sample_values: string[];
}

export interface ParsedFileResponse {
  filename: string;
  total_rows: number;
  total_columns: number;
  columns: ColumnInfo[];
  detected_name_column: string | null;
  detected_columns: Record<string, string | null>;
  preview_rows: Record<string, unknown>[];
  warnings: string[];
}

export interface FirmData {
  name: string;
  description?: string;
  industry?: string;
  stage?: string;
  revenue?: string;
  location?: string;
  valuation?: string;
  key_investors?: string;
  raw_data: Record<string, unknown>;
}

export interface ExtractedFirmsResponse {
  filename: string;
  total_firms: number;
  firms: FirmData[];
  column_mapping: Record<string, string | null>;
  warnings: string[];
}

export interface ParseOptions {
  skipRows?: number;
  nameColumn?: string;
}

export interface ExtractOptions extends ParseOptions {
  industryColumn?: string;
  stageColumn?: string;
  descriptionColumn?: string;
  valuationColumn?: string;
  keyInvestorsColumn?: string;
  revenueColumn?: string;
  locationColumn?: string;
}

// ============================================================================
// API Functions
// ============================================================================

export const uploadApi = {
  /**
   * Parse an Excel file and get column info + preview
   * This is used for the initial file upload to show preview
   */
  async parseFile(file: File, options?: ParseOptions): Promise<ParsedFileResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    // Build query params
    const params = new URLSearchParams();
    if (options?.skipRows) {
      params.append('skip_rows', options.skipRows.toString());
    }
    if (options?.nameColumn) {
      params.append('name_column', options.nameColumn);
    }
    
    const queryString = params.toString();
    const endpoint = `/upload/parse${queryString ? `?${queryString}` : ''}`;
    
    return apiClient.postForm<ParsedFileResponse>(endpoint, formData);
  },
  
  /**
   * Extract firm data from an Excel file
   * This is used when ready to filter - returns structured firm data
   */
  async extractFirms(file: File, options?: ExtractOptions): Promise<ExtractedFirmsResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    // Build query params
    const params = new URLSearchParams();
    if (options?.skipRows) {
      params.append('skip_rows', options.skipRows.toString());
    }
    if (options?.nameColumn) {
      params.append('name_column', options.nameColumn);
    }
    if (options?.industryColumn) {
      params.append('industry_column', options.industryColumn);
    }
    if (options?.stageColumn) {
      params.append('stage_column', options.stageColumn);
    }
    if (options?.descriptionColumn) {
      params.append('description_column', options.descriptionColumn);
    }
    if (options?.valuationColumn) {
      params.append('valuation_column', options.valuationColumn);
    }
    if (options?.keyInvestorsColumn) {
      params.append('key_investors_column', options.keyInvestorsColumn);
    }
    if (options?.revenueColumn) {
      params.append('revenue_column', options.revenueColumn);
    }
    if (options?.locationColumn) {
      params.append('location_column', options.locationColumn);
    }
    
    const queryString = params.toString();
    const endpoint = `/upload/extract-firms${queryString ? `?${queryString}` : ''}`;
    
    return apiClient.postForm<ExtractedFirmsResponse>(endpoint, formData);
  },
};

export default uploadApi;
