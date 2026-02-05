import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, FileSpreadsheet, Key, Search, Brain, BookOpen, CheckCircle, AlertCircle, Loader2, ChevronDown, ChevronRight, Sparkles, User } from 'lucide-react'
import { useAppStore, actions } from '../store/appStore'
import { useAnalytics, useFileUpload, useFilter } from '../hooks'
import { apiClient, thesisSuggest } from '../lib/api'
import type { FirmData } from '../lib/api'

export function RunSetupPage() {
  const navigate = useNavigate()
  const { state, dispatch } = useAppStore()
  const { logFilterQuery, logFilterResults } = useAnalytics()
  const { parsedData, isParsing, isExtracting, parseFile, extractFirms, clearData } = useFileUpload()
  const { filterFirms, isFiltering: isFilteringAPI } = useFilter()
  
  const [apiKey, setApiKey] = useState('')
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [skipRows, setSkipRows] = useState(0)
  const [useResearchDB, setUseResearchDB] = useState(false)
  
  // Column mappings
  const [columnMappings, setColumnMappings] = useState<Record<string, string | null>>({
    name: null,
    industry: null,
    stage: null,
    valuation: null,
    keyInvestors: null,
    revenue: null,
    location: null,
    description: null,
  })
  
  const updateColumnMapping = (field: string, value: string | null) => {
    setColumnMappings(prev => ({ ...prev, [field]: value }))
  }

  // VC Analyst – research thesis → suggested attributes + heuristics
  const [researchThesis, setResearchThesis] = useState('')
  const [suggestLoading, setSuggestLoading] = useState(false)
  const [suggestError, setSuggestError] = useState<string | null>(null)
  const [suggestedAttributes, setSuggestedAttributes] = useState<Record<string, string | string[]>>({})
  const [suggestedHeuristics, setSuggestedHeuristics] = useState('')

  const handleGetAnalystSuggestions = async () => {
    if (!researchThesis.trim()) {
      setSuggestError('Enter a research thesis first.')
      return
    }
    const key = apiKeyConfigured ? apiKey : undefined
    if (!key?.startsWith('sk-')) {
      setSuggestError('Configure your OpenAI API key (Step 2) before using the analyst.')
      return
    }
    setSuggestError(null)
    setSuggestLoading(true)
    try {
      const res = await thesisSuggest(researchThesis.trim(), key)
      if (res.ok && res.suggested_attributes && res.heuristics) {
        setSuggestedAttributes(res.suggested_attributes as Record<string, string | string[]>)
        setSuggestedHeuristics(res.heuristics)
      } else {
        setSuggestError(res.error || 'Could not get analyst suggestions.')
      }
    } catch (e) {
      setSuggestError(e instanceof Error ? e.message : 'Request failed.')
    } finally {
      setSuggestLoading(false)
    }
  }

  const handleUseHeuristicsForCriteria = () => {
    if (suggestedHeuristics) {
      dispatch(actions.setCriteria(suggestedHeuristics))
    }
  }
  
  // For backward compatibility
  const selectedNameColumn = columnMappings.name

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      // Parse the file via API
      await parseFile(file, { skipRows })
    }
  }, [parseFile, skipRows])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
    disabled: isParsing,
  })

  const handleFilter = async () => {
    if (!state.criteria) return
    if (!useResearchDB && !state.uploadedFile) return
    
    dispatch(actions.setIsFiltering(true))
    dispatch(actions.setError(null))
    
    try {
      let firms: FirmData[] = []
      
      if (useResearchDB) {
        // Load from research database
        const companies = await apiClient.get<Array<{ name: string; description?: string; industry?: string; stage?: string; location?: string; valuation?: number; key_investors?: string }>>('/research/companies?limit=1000')
        firms = companies.map((c) => ({
          name: c.name,
          description: c.description || '',
          industry: c.industry || '',
          stage: c.stage || '',
          revenue: '',
          location: c.location || '',
          valuation: c.valuation?.toString() || '',
          key_investors: c.key_investors || '',
          raw_data: {},
        }))
      } else if (state.uploadedFile) {
        // Extract firms from uploaded file
        const extracted = await extractFirms(state.uploadedFile, {
          skipRows,
          nameColumn: columnMappings.name || undefined,
          industryColumn: columnMappings.industry || undefined,
          stageColumn: columnMappings.stage || undefined,
          valuationColumn: columnMappings.valuation || undefined,
          keyInvestorsColumn: columnMappings.keyInvestors || undefined,
          revenueColumn: columnMappings.revenue || undefined,
          locationColumn: columnMappings.location || undefined,
          descriptionColumn: columnMappings.description || undefined,
        })
        firms = extracted?.firms || []
      }
      
      if (firms.length === 0) {
        dispatch(actions.setError(useResearchDB 
          ? 'No companies found in research database. Run the scraper first.' 
          : 'No firms found in file. Check column mapping.'))
        dispatch(actions.setIsFiltering(false))
        return
      }
      
      // Call real filter API
      const response = await filterFirms(state.criteria, firms, 10)
      
      if (!response) {
        // Error already handled by useFilter hook
        return
      }
      
      // Log analytics (fire and forget)
      const queryId = await logFilterQuery(
        state.criteria,
        response.metadata.total_processed,
        response.metadata.processing_time_ms,
        response.metadata.filter_method,
        { usedCache: response.metadata.cache_hit, usedRag: false }
      )
      if (queryId) {
        // Map to the expected format for analytics
        const analyticsResults = response.results.map(r => ({
          ...r,
          industry: r.industry || 'Unknown',
          stage: r.stage || 'Unknown',
        }))
        logFilterResults(queryId, analyticsResults)
      }
      
      // Navigate to results
      navigate('/results')
    } catch (err) {
      dispatch(actions.setError(err instanceof Error ? err.message : 'Filter failed'))
      dispatch(actions.setIsFiltering(false))
    }
  }

  const handleSaveApiKey = () => {
    if (apiKey.startsWith('sk-')) {
      setApiKeyConfigured(true)
      dispatch(actions.setApiKey(apiKey))
    }
  }

  const handleRemoveFile = (e: React.MouseEvent) => {
    e.stopPropagation()
    clearData()
  }

  const handleReparse = async () => {
    if (state.uploadedFile) {
      await parseFile(state.uploadedFile, { 
        skipRows, 
        nameColumn: selectedNameColumn || undefined 
      })
    }
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Run Setup</h1>
        <p className="mt-1 text-gray-500">Upload your firm data and configure filtering criteria</p>
      </div>

      {/* Error Banner */}
      {state.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-800 font-medium">Error</p>
            <p className="text-red-600 text-sm">{state.error}</p>
          </div>
        </div>
      )}

      {/* Step 1: Data Source Selection */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
            <Upload className="w-4 h-4 text-blue-600" />
          </div>
          <h2 className="text-lg font-medium text-gray-900">Step 1: Choose Data Source</h2>
        </div>

        {/* Data Source Toggle */}
        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="dataSource"
                  checked={!useResearchDB}
                  onChange={() => setUseResearchDB(false)}
                  className="w-4 h-4 text-blue-600"
                />
                <span className="font-medium text-gray-700">Upload Excel File</span>
              </label>
              <p className="text-sm text-gray-500 ml-6 mt-1">Upload your own company data</p>
            </div>
            <div>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="dataSource"
                  checked={useResearchDB}
                  onChange={() => setUseResearchDB(true)}
                  className="w-4 h-4 text-blue-600"
                />
                <span className="font-medium text-gray-700">Use Research Database</span>
              </label>
              <p className="text-sm text-gray-500 ml-6 mt-1">Use scraped companies from public sources</p>
            </div>
          </div>
        </div>

        {/* File Upload Section (only show if not using research DB) */}
        {!useResearchDB && (
          <>
            <div className="flex items-center space-x-2 mb-4">
              <h3 className="text-md font-medium text-gray-700">Upload Excel File</h3>
              {parsedData && <CheckCircle className="w-5 h-5 text-green-500" />}
            </div>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isParsing
              ? 'border-blue-400 bg-blue-50'
              : isDragActive 
                ? 'border-blue-500 bg-blue-50' 
                : parsedData 
                  ? 'border-green-300 bg-green-50' 
                  : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          
          {isParsing ? (
            <div className="flex flex-col items-center">
              <Loader2 className="w-12 h-12 text-blue-500 mb-3 animate-spin" />
              <p className="font-medium text-blue-700">Parsing file...</p>
              <p className="text-sm text-blue-500 mt-1">Analyzing columns and data structure</p>
            </div>
          ) : parsedData ? (
            <div className="flex flex-col items-center">
              <FileSpreadsheet className="w-12 h-12 text-green-500 mb-3" />
              <p className="font-medium text-gray-900">{parsedData.filename}</p>
              <p className="text-sm text-gray-500">{parsedData.total_rows} rows · {parsedData.total_columns} columns</p>
              <button 
                onClick={handleRemoveFile}
                className="mt-2 text-sm text-red-600 hover:text-red-700"
              >
                Remove
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <Upload className="w-12 h-12 text-gray-400 mb-3" />
              <p className="text-gray-600">
                {isDragActive ? 'Drop the file here' : 'Drag & drop your Excel file here, or click to browse'}
              </p>
              <p className="text-sm text-gray-400 mt-1">Supported formats: .xlsx, .xls</p>
            </div>
          )}
        </div>

        {/* Warnings */}
        {parsedData?.warnings && parsedData.warnings.length > 0 && (
          <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm font-medium text-amber-800">Warnings:</p>
            <ul className="mt-1 text-sm text-amber-700">
              {parsedData.warnings.map((warning, i) => (
                <li key={i}>• {warning}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Data Preview */}
        {parsedData && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 mb-3">📊 Data Preview</h3>
            
            {/* Column Detection Status */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
              {Object.entries(parsedData.detected_columns).map(([field, column]) => (
                <div key={field} className="flex items-center space-x-1 text-xs">
                  {column ? (
                    <CheckCircle className="w-3 h-3 text-green-500" />
                  ) : (
                    <AlertCircle className="w-3 h-3 text-gray-300" />
                  )}
                  <span className={column ? 'text-gray-700' : 'text-gray-400'}>
                    {field}: {column || 'not found'}
                  </span>
                </div>
              ))}
            </div>
            
            {/* Preview Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead className="bg-gray-100">
                  <tr>
                    {parsedData.columns.slice(0, 6).map((col) => (
                      <th key={col.name} className="px-2 py-1 text-left font-medium text-gray-600 truncate max-w-[150px]">
                        {col.name}
                        {col.name === parsedData.detected_name_column && (
                          <span className="ml-1 text-green-600">(Name)</span>
                        )}
                      </th>
                    ))}
                    {parsedData.columns.length > 6 && (
                      <th className="px-2 py-1 text-gray-400">+{parsedData.columns.length - 6} more</th>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {parsedData.preview_rows.slice(0, 5).map((row, i) => (
                    <tr key={i}>
                      {parsedData.columns.slice(0, 6).map((col) => (
                        <td key={col.name} className="px-2 py-1 text-gray-700 truncate max-w-[150px]">
                          {String(row[col.name] || '')}
                        </td>
                      ))}
                      {parsedData.columns.length > 6 && <td className="px-2 py-1 text-gray-400">...</td>}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <p className="mt-2 text-xs text-gray-500">
              Showing first 5 of {parsedData.total_rows} rows
            </p>
          </div>
        )}

        {/* Advanced Options - Auto-expand if name column not detected */}
        {state.uploadedFile && (
          <div className="mt-4">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center text-sm text-gray-600 hover:text-gray-800"
            >
              {showAdvanced ? <ChevronDown className="w-4 h-4 mr-1" /> : <ChevronRight className="w-4 h-4 mr-1" />}
              Column Mapping & Options
              {!parsedData?.detected_name_column && (
                <span className="ml-2 text-amber-600 text-xs">(Action required)</span>
              )}
            </button>
            
            {(showAdvanced || !parsedData?.detected_name_column) && parsedData && (
              <div className="mt-3 p-4 bg-gray-50 rounded-lg space-y-4">
                {/* Company Name Column - Most Important */}
                <div className="p-3 border border-blue-200 bg-blue-50 rounded-lg">
                  <label className="block text-sm font-medium text-blue-800 mb-2">
                    🏢 Company Name Column <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={columnMappings.name || parsedData.detected_name_column || ''}
                    onChange={(e) => updateColumnMapping('name', e.target.value || null)}
                    className="w-full px-3 py-2 border border-blue-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">-- Select the column containing company names --</option>
                    {parsedData.columns.map((col) => (
                      <option key={col.name} value={col.name}>
                        {col.name} (e.g., "{col.sample_values[0] || 'empty'}")
                      </option>
                    ))}
                  </select>
                  {parsedData.detected_name_column && !columnMappings.name && (
                    <p className="mt-1 text-xs text-blue-600">
                      Auto-detected: <strong>{parsedData.detected_name_column}</strong>
                    </p>
                  )}
                  {!parsedData.detected_name_column && !columnMappings.name && (
                    <p className="mt-1 text-xs text-amber-600">
                      ⚠️ Could not auto-detect. Please select the correct column.
                    </p>
                  )}
                </div>
                
                {/* Column Mappings Grid */}
                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-gray-700">📊 Column Mappings</h4>
                  <p className="text-xs text-gray-500">Map your Excel columns to the correct data fields. Leave as "Auto-detect" to use automatic detection.</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {/* Industry */}
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Industry / Sector</label>
                      <select
                        value={columnMappings.industry || ''}
                        onChange={(e) => updateColumnMapping('industry', e.target.value || null)}
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="">Auto-detect {parsedData.detected_columns.industry ? `(${parsedData.detected_columns.industry})` : ''}</option>
                        {parsedData.columns.map((col) => (
                          <option key={col.name} value={col.name}>{col.name}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Stage */}
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Funding Stage</label>
                      <select
                        value={columnMappings.stage || ''}
                        onChange={(e) => updateColumnMapping('stage', e.target.value || null)}
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="">Auto-detect {parsedData.detected_columns.stage ? `(${parsedData.detected_columns.stage})` : ''}</option>
                        {parsedData.columns.map((col) => (
                          <option key={col.name} value={col.name}>{col.name}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Valuation */}
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">💰 Valuation</label>
                      <select
                        value={columnMappings.valuation || ''}
                        onChange={(e) => updateColumnMapping('valuation', e.target.value || null)}
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="">Auto-detect {parsedData.detected_columns.valuation ? `(${parsedData.detected_columns.valuation})` : ''}</option>
                        {parsedData.columns.map((col) => (
                          <option key={col.name} value={col.name}>{col.name}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Key Investors */}
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">🏦 Key Investors</label>
                      <select
                        value={columnMappings.keyInvestors || ''}
                        onChange={(e) => updateColumnMapping('keyInvestors', e.target.value || null)}
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="">Auto-detect {parsedData.detected_columns.key_investors ? `(${parsedData.detected_columns.key_investors})` : ''}</option>
                        {parsedData.columns.map((col) => (
                          <option key={col.name} value={col.name}>{col.name}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Revenue */}
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Revenue / ARR</label>
                      <select
                        value={columnMappings.revenue || ''}
                        onChange={(e) => updateColumnMapping('revenue', e.target.value || null)}
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="">Auto-detect {parsedData.detected_columns.revenue ? `(${parsedData.detected_columns.revenue})` : ''}</option>
                        {parsedData.columns.map((col) => (
                          <option key={col.name} value={col.name}>{col.name}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Location */}
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Location / HQ</label>
                      <select
                        value={columnMappings.location || ''}
                        onChange={(e) => updateColumnMapping('location', e.target.value || null)}
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="">Auto-detect {parsedData.detected_columns.location ? `(${parsedData.detected_columns.location})` : ''}</option>
                        {parsedData.columns.map((col) => (
                          <option key={col.name} value={col.name}>{col.name}</option>
                        ))}
                      </select>
                    </div>
                    
                    {/* Description */}
                    <div className="md:col-span-2 lg:col-span-3">
                      <label className="block text-xs font-medium text-gray-600 mb-1">Description / About</label>
                      <select
                        value={columnMappings.description || ''}
                        onChange={(e) => updateColumnMapping('description', e.target.value || null)}
                        className="w-full px-2 py-1.5 border border-gray-300 rounded text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="">Auto-detect {parsedData.detected_columns.description ? `(${parsedData.detected_columns.description})` : ''}</option>
                        {parsedData.columns.map((col) => (
                          <option key={col.name} value={col.name}>{col.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
                
                {/* Skip Rows */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Skip Rows
                  </label>
                  <input
                    type="number"
                    value={skipRows}
                    onChange={(e) => setSkipRows(parseInt(e.target.value) || 0)}
                    min={0}
                    max={50}
                    className="w-24 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">Skip metadata rows at the top of the file</p>
                </div>
                
                <button
                  onClick={handleReparse}
                  disabled={isParsing}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
                >
                  {isParsing ? 'Re-parsing...' : '🔄 Apply Column Mapping'}
                </button>
              </div>
            )}
          </div>
        )}
        </>
        )}

        {/* Research Database Info (only show if using research DB) */}
        {useResearchDB && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-green-800">Using Research Database</p>
                <p className="text-sm text-green-700 mt-1">
                  Companies will be loaded from the research database. Make sure you've run the scraper first.
                </p>
                <a 
                  href="/research" 
                  className="text-sm text-green-600 hover:text-green-700 underline mt-2 inline-block"
                >
                  Go to Research Dashboard →
                </a>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Step 2: API Key */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
            <Key className="w-4 h-4 text-blue-600" />
          </div>
          <h2 className="text-lg font-medium text-gray-900">Step 2: Configure API Key</h2>
          {apiKeyConfigured && <CheckCircle className="w-5 h-5 text-green-500" />}
        </div>

        {apiKeyConfigured ? (
          <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="text-green-700 font-medium">API Key configured</span>
              <span className="text-gray-500 text-sm">sk-•••••••••••••{apiKey.slice(-4)}</span>
            </div>
            <button 
              onClick={() => { setApiKeyConfigured(false); setApiKey('') }}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Change
            </button>
          </div>
        ) : (
          <div className="flex space-x-3">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button 
              onClick={handleSaveApiKey}
              disabled={!apiKey.startsWith('sk-')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                apiKey.startsWith('sk-')
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              Save Key
            </button>
          </div>
        )}
          {!apiKeyConfigured && (
            <p className="mt-2 text-sm text-gray-500">
              Get your API key from <a href="https://platform.openai.com/api-keys" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">OpenAI Platform</a>
            </p>
          )}
        </div>

        {/* Research Thesis & VC Analyst */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
              <User className="w-4 h-4 text-amber-600" />
            </div>
            <h2 className="text-lg font-medium text-gray-900">Research Thesis & VC Analyst</h2>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Describe the logic behind the companies you&apos;re looking for. A VC analyst (B2B enterprise, 10+ years) will suggest attributes and heuristics to drive search.
          </p>
          <textarea
            value={researchThesis}
            onChange={(e) => { setResearchThesis(e.target.value); setSuggestError(null) }}
            placeholder="e.g., PLG SaaS in dev tools and infra. Seed to Series A, US-first. Strong technical founders, early traction with developers. We like companies that could become default in a category."
            className="w-full h-24 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 resize-none"
          />
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleGetAnalystSuggestions}
              disabled={suggestLoading || !researchThesis.trim() || !apiKeyConfigured}
              className="inline-flex items-center px-4 py-2 rounded-lg font-medium bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {suggestLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Sparkles className="w-4 h-4 mr-2" />}
              {suggestLoading ? 'Getting suggestions...' : 'Get analyst suggestions'}
            </button>
            {suggestError && (
              <span className="text-sm text-red-600">{suggestError}</span>
            )}
          </div>
          {Object.keys(suggestedAttributes).length > 0 && (
            <div className="mt-4 p-4 bg-amber-50 rounded-lg border border-amber-200 space-y-3">
              <h3 className="text-sm font-medium text-amber-900">Suggested attributes</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {['company_size', 'funding_stage', 'target_investors', 'geography', 'industry_vertical', 'exclusions'].map((k) => {
                  const v = suggestedAttributes[k]
                  const str = Array.isArray(v) ? (v as string[]).join(', ') : typeof v === 'string' ? v : ''
                  return (
                    <div key={k}>
                      <label className="block text-xs font-medium text-gray-600 mb-1 capitalize">
                        {k.replace(/_/g, ' ')}
                      </label>
                      <input
                        type="text"
                        value={str}
                        onChange={(e) => setSuggestedAttributes((prev) => ({ ...prev, [k]: e.target.value }))}
                        className="w-full px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                      />
                    </div>
                  )
                })}
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Heuristics (qualitative match logic)</label>
                <textarea
                  value={suggestedHeuristics}
                  onChange={(e) => setSuggestedHeuristics(e.target.value)}
                  className="w-full h-20 px-3 py-2 border border-gray-300 rounded text-sm resize-none"
                />
              </div>
              <button
                type="button"
                onClick={handleUseHeuristicsForCriteria}
                disabled={!suggestedHeuristics}
                className="text-sm text-amber-700 hover:text-amber-800 font-medium"
              >
                Use heuristics as filtering criteria →
              </button>
            </div>
          )}
        </div>

        {/* Step 3: Criteria */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <Search className="w-4 h-4 text-blue-600" />
            </div>
            <h2 className="text-lg font-medium text-gray-900">Step 3: Enter Filtering Criteria</h2>
            {state.criteria.length > 10 && <CheckCircle className="w-5 h-5 text-green-500" />}
          </div>

        <textarea
          value={state.criteria}
          onChange={(e) => dispatch(actions.setCriteria(e.target.value))}
          placeholder="e.g., Looking for AI/ML startups with revenue >$1M, Series A stage, B2B focus, strong technical team. Or use 'Use heuristics as filtering criteria' from the Analyst above."
          className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
        />
        <p className="mt-2 text-sm text-gray-500">
          💡 Tip: Be specific about industry, stage, revenue metrics, and team characteristics. Use the VC Analyst to generate criteria from a research thesis.
        </p>
      </div>

      {/* Step 4: Optional Enhancements */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
            <Brain className="w-4 h-4 text-gray-600" />
          </div>
          <h2 className="text-lg font-medium text-gray-900">Step 4: Optional Enhancements</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
            <div className="flex items-center space-x-2 mb-2">
              <BookOpen className="w-5 h-5 text-gray-400" />
              <span className="font-medium text-gray-700">RAG Documents</span>
            </div>
            <p className="text-sm text-gray-500">0 documents loaded</p>
            <button className="mt-2 text-sm text-blue-600 hover:text-blue-700">
              + Add documents
            </button>
          </div>
          
          <div className="p-4 border border-green-200 rounded-lg bg-green-50">
            <div className="flex items-center space-x-2 mb-2">
              <Brain className="w-5 h-5 text-green-500" />
              <span className="font-medium text-gray-700">VC Knowledge Base</span>
            </div>
            <p className="text-sm text-green-600">✅ 1,234 chunks loaded</p>
            <button className="mt-2 text-sm text-gray-500 hover:text-gray-700">
              🔄 Rebuild
            </button>
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 text-center">
        <button
          onClick={handleFilter}
          disabled={(!useResearchDB && !parsedData) || !state.criteria || state.isFiltering || isExtracting || isFilteringAPI}
          className={`px-8 py-3 rounded-lg font-medium text-lg transition-all ${
            (useResearchDB || parsedData) && state.criteria && !state.isFiltering && !isExtracting && !isFilteringAPI
              ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-xl'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          {state.isFiltering || isExtracting || isFilteringAPI ? (
            <span className="flex items-center justify-center">
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              {isExtracting ? 'Extracting firms...' : 'Filtering with AI...'}
            </span>
          ) : (
            '🔍 Filter Top 10 Firms'
          )}
        </button>
        <p className="mt-2 text-sm text-gray-500">
          {useResearchDB
            ? 'Will analyze companies from research database · Estimated time: ~30 seconds'
            : parsedData 
              ? `Will analyze ${parsedData.total_rows} firms · Estimated time: ~30 seconds`
              : 'Estimated time: ~30 seconds'
          }
        </p>
        
        {((!useResearchDB && !parsedData) || !state.criteria) && (
          <div className="mt-4 flex items-center justify-center space-x-2 text-amber-600">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">
              {!useResearchDB && !parsedData && !state.criteria 
                ? 'Choose data source and enter criteria to continue' 
                : !useResearchDB && !parsedData
                  ? 'Upload an Excel file or use research database'
                  : !state.criteria
                    ? 'Enter filtering criteria to continue'
                    : ''}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
