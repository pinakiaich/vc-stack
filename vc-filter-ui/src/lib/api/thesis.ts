/**
 * VC Analyst – Research thesis → suggested attributes + heuristics
 */

import { apiClient } from './client';

export interface ThesisSuggestRequest {
  thesis: string
  api_key?: string
}

export interface ThesisSuggestResponse {
  ok: boolean
  suggested_attributes?: Record<string, unknown>
  heuristics?: string
  error?: string
}

export async function thesisSuggest(
  thesis: string,
  apiKey?: string
): Promise<ThesisSuggestResponse> {
  return apiClient.post<ThesisSuggestResponse>('/research/thesis/suggest', {
    thesis,
    api_key: apiKey || undefined,
  })
}
