/**
 * API Services Index
 * Export all API services from a single entry point
 */

export { apiClient, ApiError } from './client';
export { dealsApi } from './deals';
export { researchApi } from './research';
export { companiesApi } from './companies';
export { analyticsApi } from './analytics';
export { uploadApi } from './upload';
export { filterApi } from './filter';
export { thesisSuggest } from './thesis';
export type { ThesisSuggestRequest, ThesisSuggestResponse } from './thesis';
export type { 
  ColumnInfo, 
  ParsedFileResponse, 
  FirmData, 
  ExtractedFirmsResponse,
  ParseOptions,
  ExtractOptions 
} from './upload';
export type {
  FilterRequest,
  FilteredFirm,
  FilterMetadata,
  FilterResponse,
} from './filter';

// Re-export types
export type * from '../../types';
