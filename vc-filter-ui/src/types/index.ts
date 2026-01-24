// ============================================================================
// Core Types - Matching Backend Models
// ============================================================================

// Company
export interface Company {
  id: number;
  name: string;
  description?: string;
  stage?: string;
  revenue?: string;
  industry?: string;
  location?: string;
}

export interface CompanyCreate {
  name: string;
  description?: string;
  stage?: string;
  revenue?: string;
  industry?: string;
  location?: string;
}

// Deal (v2)
export interface Deal {
  id: number;
  name: string;
  source?: string;
  owner?: string;
  sector?: string;
  stage?: string;
  status: string;
  created_at: string;
}

export interface DealCreate {
  name: string;
  source?: string;
  owner?: string;
  sector?: string;
  stage?: string;
  status?: string;
}

// Research Finding
export interface ResearchFinding {
  id: number;
  deal_id: number;
  category?: string;
  source_type?: string;
  content: string;
  citation?: string;
  created_at: string;
}

export interface ResearchFindingCreate {
  deal_id: number;
  category?: string;
  source_type?: string;
  content: string;
  citation?: string;
}

// Filter Query (Analytics)
export interface FilterQuery {
  id: number;
  user_id?: string;
  criteria: string;
  total_firms_analyzed: number;
  processing_time_ms: number;
  filter_method: string;
  used_cache: boolean;
  used_rag: boolean;
  created_at: string;
}

export interface FilterQueryCreate {
  criteria: string;
  total_firms: number;
  processing_time_ms: number;
  filter_method: string;
  used_cache?: boolean;
  used_rag?: boolean;
  user_id?: string;
}

// Filter Result
export interface FilterResult {
  id: number;
  query_id: number;
  company_id: number;
  company_name: string;
  score: number;
  rank: number;
  reason?: string;
  vector_similarity?: number;
  created_at: string;
}

// ============================================================================
// Frontend-Specific Types
// ============================================================================

// Firm result as displayed in the UI
export interface FirmResult {
  id: string;
  rank: number;
  name: string;
  score: number;
  reason: string;
  industry: string;
  stage: string;
  revenue?: string;
  location?: string;
  description?: string;
  valuation?: string;
  keyInvestors?: string;
  opportunityScore?: number;
  exitProbabilityScore?: number;
}

// Research data structure for memo view
export interface ResearchData {
  companyInfo: {
    name: string;
    country: string;
    industry: string;
  };
  quantitativeData: {
    tam?: string;
    sam?: string;
    cagr?: string;
    revenue?: string;
    ndr?: string;
    funding?: string;
    valuation?: string;
    employees?: string;
    [key: string]: string | undefined;
  };
  industryBackground: string;
  companyBackground: string;
  founderProfile: string;
  competition: string;
}

// Filter request payload
export interface FilterRequest {
  criteria: string;
  file: File;
  options?: {
    skipRows?: number;
    nameColumn?: string;
  };
}

// Filter response
export interface FilterResponse {
  results: FirmResult[];
  metadata: {
    totalProcessed: number;
    processingTimeMs: number;
    cacheHitRate?: number;
    filterMethod: string;
  };
}

// API Error
export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}
