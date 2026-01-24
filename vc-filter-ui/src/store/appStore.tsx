/**
 * Application State Store
 * Simple state management using React Context + useReducer pattern
 */

import { createContext, useContext, useReducer, ReactNode } from 'react';
import type { FirmResult, Deal, FilterResponse } from '../types';

// ============================================================================
// State Types
// ============================================================================

interface AppState {
  // API Connection
  apiConnected: boolean;
  apiKey: string | null;
  
  // File Upload
  uploadedFile: File | null;
  parsedData: {
    firms: Array<Record<string, unknown>>;
    columns: string[];
    totalRows: number;
  } | null;
  
  // Filter
  criteria: string;
  filterResults: FirmResult[];
  filterMetadata: {
    totalProcessed: number;
    processingTimeMs: number;
    cacheHitRate: number;
    filterMethod: string;
  } | null;
  isFiltering: boolean;
  
  // Deal Workspace
  selectedDeal: Deal | null;
  deals: Deal[];
  
  // UI State
  isLoading: boolean;
  error: string | null;
}

// ============================================================================
// Actions
// ============================================================================

type Action =
  | { type: 'SET_API_CONNECTED'; payload: boolean }
  | { type: 'SET_API_KEY'; payload: string | null }
  | { type: 'SET_UPLOADED_FILE'; payload: File | null }
  | { type: 'SET_PARSED_DATA'; payload: AppState['parsedData'] }
  | { type: 'SET_CRITERIA'; payload: string }
  | { type: 'SET_FILTER_RESULTS'; payload: FilterResponse }
  | { type: 'CLEAR_FILTER_RESULTS' }
  | { type: 'SET_IS_FILTERING'; payload: boolean }
  | { type: 'SET_SELECTED_DEAL'; payload: Deal | null }
  | { type: 'SET_DEALS'; payload: Deal[] }
  | { type: 'ADD_DEAL'; payload: Deal }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'RESET' };

// ============================================================================
// Initial State
// ============================================================================

const initialState: AppState = {
  apiConnected: false,
  apiKey: null,
  uploadedFile: null,
  parsedData: null,
  criteria: '',
  filterResults: [],
  filterMetadata: null,
  isFiltering: false,
  selectedDeal: null,
  deals: [],
  isLoading: false,
  error: null,
};

// ============================================================================
// Reducer
// ============================================================================

function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_API_CONNECTED':
      return { ...state, apiConnected: action.payload };
    
    case 'SET_API_KEY':
      return { ...state, apiKey: action.payload };
    
    case 'SET_UPLOADED_FILE':
      return { ...state, uploadedFile: action.payload };
    
    case 'SET_PARSED_DATA':
      return { ...state, parsedData: action.payload };
    
    case 'SET_CRITERIA':
      return { ...state, criteria: action.payload };
    
    case 'SET_FILTER_RESULTS':
      return {
        ...state,
        filterResults: action.payload.results,
        filterMetadata: action.payload.metadata,
        isFiltering: false,
      };
    
    case 'CLEAR_FILTER_RESULTS':
      return { ...state, filterResults: [], filterMetadata: null };
    
    case 'SET_IS_FILTERING':
      return { ...state, isFiltering: action.payload };
    
    case 'SET_SELECTED_DEAL':
      return { ...state, selectedDeal: action.payload };
    
    case 'SET_DEALS':
      return { ...state, deals: action.payload };
    
    case 'ADD_DEAL':
      return { ...state, deals: [action.payload, ...state.deals] };
    
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    
    case 'RESET':
      return initialState;
    
    default:
      return state;
  }
}

// ============================================================================
// Context
// ============================================================================

interface AppContextValue {
  state: AppState;
  dispatch: React.Dispatch<Action>;
}

const AppContext = createContext<AppContextValue | undefined>(undefined);

// ============================================================================
// Provider
// ============================================================================

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

export function useAppStore() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppStore must be used within an AppProvider');
  }
  return context;
}

// ============================================================================
// Action Creators (Helper functions)
// ============================================================================

export const actions = {
  setApiConnected: (connected: boolean): Action => ({ type: 'SET_API_CONNECTED', payload: connected }),
  setApiKey: (key: string | null): Action => ({ type: 'SET_API_KEY', payload: key }),
  setUploadedFile: (file: File | null): Action => ({ type: 'SET_UPLOADED_FILE', payload: file }),
  setParsedData: (data: AppState['parsedData']): Action => ({ type: 'SET_PARSED_DATA', payload: data }),
  setCriteria: (criteria: string): Action => ({ type: 'SET_CRITERIA', payload: criteria }),
  setFilterResults: (response: FilterResponse): Action => ({ type: 'SET_FILTER_RESULTS', payload: response }),
  clearFilterResults: (): Action => ({ type: 'CLEAR_FILTER_RESULTS' }),
  setIsFiltering: (filtering: boolean): Action => ({ type: 'SET_IS_FILTERING', payload: filtering }),
  setSelectedDeal: (deal: Deal | null): Action => ({ type: 'SET_SELECTED_DEAL', payload: deal }),
  setDeals: (deals: Deal[]): Action => ({ type: 'SET_DEALS', payload: deals }),
  addDeal: (deal: Deal): Action => ({ type: 'ADD_DEAL', payload: deal }),
  setLoading: (loading: boolean): Action => ({ type: 'SET_LOADING', payload: loading }),
  setError: (error: string | null): Action => ({ type: 'SET_ERROR', payload: error }),
  reset: (): Action => ({ type: 'RESET' }),
};
