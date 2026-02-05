/**
 * File Upload Hook
 * Handles Excel file parsing and firm extraction
 */

import { useState, useCallback } from 'react';
import { uploadApi, type ParsedFileResponse, type ExtractedFirmsResponse, type ParseOptions, type ExtractOptions } from '../lib/api';
import { useAppStore, actions } from '../store/appStore';

interface UseFileUploadReturn {
  // State
  parsedData: ParsedFileResponse | null;
  extractedFirms: ExtractedFirmsResponse | null;
  isParsing: boolean;
  isExtracting: boolean;
  error: string | null;
  
  // Actions
  parseFile: (file: File, options?: ParseOptions) => Promise<ParsedFileResponse | null>;
  extractFirms: (file: File, options?: ExtractOptions) => Promise<ExtractedFirmsResponse | null>;
  clearData: () => void;
}

export function useFileUpload(): UseFileUploadReturn {
  const { dispatch } = useAppStore();
  
  const [parsedData, setParsedData] = useState<ParsedFileResponse | null>(null);
  const [extractedFirms, setExtractedFirms] = useState<ExtractedFirmsResponse | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  /**
   * Parse a file to get column info and preview
   */
  const parseFile = useCallback(async (
    file: File, 
    options?: ParseOptions
  ): Promise<ParsedFileResponse | null> => {
    setIsParsing(true);
    setError(null);
    
    try {
      const result = await uploadApi.parseFile(file, options);
      setParsedData(result);
      
      // Update app store with parsed data
      dispatch(actions.setUploadedFile(file));
      dispatch(actions.setParsedData({
        firms: [], // Will be populated after extraction
        columns: result.columns.map(c => c.name),
        totalRows: result.total_rows,
      }));
      
      // Log warnings
      if (result.warnings.length > 0) {
        console.warn('File parsing warnings:', result.warnings);
      }
      
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to parse file';
      setError(message);
      dispatch(actions.setError(message));
      return null;
    } finally {
      setIsParsing(false);
    }
  }, [dispatch]);
  
  /**
   * Extract firms from a file for filtering
   */
  const extractFirms = useCallback(async (
    file: File,
    options?: ExtractOptions
  ): Promise<ExtractedFirmsResponse | null> => {
    setIsExtracting(true);
    setError(null);
    
    try {
      const result = await uploadApi.extractFirms(file, options);
      setExtractedFirms(result);
      
      // Update app store with extracted firms
      dispatch(actions.setParsedData({
        firms: result.firms.map(f => f.raw_data),
        columns: Object.keys(result.column_mapping),
        totalRows: result.total_firms,
      }));
      
      // Log warnings
      if (result.warnings.length > 0) {
        console.warn('Firm extraction warnings:', result.warnings);
      }
      
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to extract firms';
      setError(message);
      dispatch(actions.setError(message));
      return null;
    } finally {
      setIsExtracting(false);
    }
  }, [dispatch]);
  
  /**
   * Clear all upload data
   */
  const clearData = useCallback(() => {
    setParsedData(null);
    setExtractedFirms(null);
    setError(null);
    dispatch(actions.setUploadedFile(null));
    dispatch(actions.setParsedData(null));
  }, [dispatch]);
  
  return {
    parsedData,
    extractedFirms,
    isParsing,
    isExtracting,
    error,
    parseFile,
    extractFirms,
    clearData,
  };
}

export default useFileUpload;
