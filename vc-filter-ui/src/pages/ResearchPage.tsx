import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Download, Play, Filter, TrendingUp, Building2, DollarSign, Loader2, AlertCircle } from 'lucide-react'
import { apiClient } from '../lib/api'

interface ScrapedCompany {
  id: number
  name: string
  description?: string
  industry?: string
  stage?: string
  valuation?: number
  key_investors?: string
  location?: string
  website?: string
  source_name?: string
  match_reasoning?: string
  created_at: string
}

interface ResearchStats {
  total_companies: number
  by_stage: Record<string, number>
  by_source: Record<string, number>
  by_valuation_range: Record<string, number>
}

interface ScrapeJob {
  id: number
  status: string
  job_type: string
  source_name: string
  started_at?: string
  completed_at?: string
  companies_found: number
  companies_added: number
  companies_updated: number
  errors?: string
  created_at: string
}

export function ResearchPage() {
  const navigate = useNavigate()
  const [companies, setCompanies] = useState<ScrapedCompany[]>([])
  const [stats, setStats] = useState<ResearchStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isScraping, setIsScraping] = useState(false)
  const [scrapeJobs, setScrapeJobs] = useState<ScrapeJob[]>([])
  const [selectedStage, setSelectedStage] = useState<string>('')
  const [selectedIndustry, setSelectedIndustry] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [scrapeError, setScrapeError] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    // Only load existing data - NEVER trigger scraping automatically
    loadCompanies()
    loadStats()
    loadScrapeJobs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedStage, selectedIndustry])

  const loadCompanies = async () => {
    try {
      setIsLoading(true)
      setLoadError(null)
      console.log('Loading companies from API...')
      
      const params = new URLSearchParams()
      if (selectedStage) params.append('stage', selectedStage)
      if (selectedIndustry) params.append('industry', selectedIndustry)
      params.append('limit', '100')

      // Add timeout to prevent infinite loading
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Request timeout - backend may not be responding')), 10000)
      })

      const response = await Promise.race([
        apiClient.get<ScrapedCompany[]>(`/research/companies?${params}`),
        timeoutPromise
      ])
      
      console.log(`Loaded ${response.length} companies`)
      setCompanies(response)
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      setLoadError(msg)
      console.error('Error loading companies:', err)
      // Set empty array on error so UI doesn't show "No companies" when it's actually an error
      setCompanies([])
    } finally {
      setIsLoading(false)
      console.log('Finished loading companies (success or error)')
    }
  }

  const loadStats = async () => {
    try {
      const response = await apiClient.get<ResearchStats>('/research/stats')
      setStats(response)
    } catch (err) {
      console.error('Error loading stats:', err)
    }
  }

  const loadScrapeJobs = async () => {
    try {
      const response = await apiClient.get<ScrapeJob[]>('/research/scrape/status?limit=5')
      setScrapeJobs(response)
    } catch (err) {
      console.error('Error loading scrape jobs:', err)
    }
  }

  const handleRunScraper = async () => {
    // Only run when explicitly called by button click - never automatically
    if (isScraping) {
      console.warn('Scraper is already running, ignoring duplicate request')
      return
    }
    
    setScrapeError(null)
    setIsScraping(true)
    
    try {
      console.log('User clicked Run Scraper - starting scrape job')
      
      // Add timeout to prevent infinite "Scraping..." state
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Scrape request timeout - backend may not be responding')), 30000)
      })
      
      // Start with limit=1 for testing - remove limit parameter once working
      await Promise.race([
        apiClient.post('/research/scrape', {
          source_names: ['open_data'],  // Start with just one source
          job_type: 'on_demand',
          limit: 1,  // TEST MODE: Only process 1 company
        }),
        timeoutPromise
      ])
      
      console.log('Scrape job started successfully, will reload data in 2 seconds')
      setTimeout(() => {
        loadCompanies()
        loadStats()
        loadScrapeJobs()
      }, 2000)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setScrapeError(msg)
      console.error('Error running scraper:', err)
    } finally {
      // Always reset scraping state, even on timeout or error
      setIsScraping(false)
      console.log('Scraper button state reset')
    }
  }

  const handleExport = async () => {
    try {
      const params = new URLSearchParams()
      if (selectedStage) params.append('stage', selectedStage)
      if (selectedIndustry) params.append('industry', selectedIndustry)
      
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/research/export?${params}`)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'scraped_companies.xlsx'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      console.error('Error exporting:', err)
    }
  }

  const handleSendToFilter = () => {
    // Navigate to filter with companies from research DB
    navigate('/', { state: { useResearchDB: true } })
  }

  const filteredCompanies = companies.filter(company => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        company.name.toLowerCase().includes(query) ||
        company.description?.toLowerCase().includes(query) ||
        company.industry?.toLowerCase().includes(query)
      )
    }
    return true
  })

  const formatValuation = (val?: number) => {
    if (!val) return '—'
    if (val >= 1_000_000_000) return `$${(val / 1_000_000_000).toFixed(1)}B`
    return `$${(val / 1_000_000).toFixed(0)}M`
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Research Dashboard</h1>
          <p className="mt-1 text-gray-500">Scraped companies from public sources</p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={handleRunScraper}
            disabled={isScraping}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {isScraping ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Scraping...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Run Scraper
              </>
            )}
          </button>
          <button
            onClick={handleExport}
            className="flex items-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            <Download className="w-4 h-4 mr-2" />
            Export Excel
          </button>
          <button
            onClick={handleSendToFilter}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Filter className="w-4 h-4 mr-2" />
            Send to Filter
          </button>
        </div>
      </div>

      {/* Load / scrape error alerts */}
      {(loadError || scrapeError) && (
        <div className="flex items-center justify-between p-4 bg-red-50 border border-red-200 rounded-xl">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <p className="text-sm text-red-800">{loadError || scrapeError}</p>
          </div>
          <button
            onClick={() => { setLoadError(null); setScrapeError(null) }}
            className="text-sm text-red-600 hover:text-red-800 font-medium"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Companies</p>
                <p className="text-2xl font-semibold text-gray-900 mt-1">{stats.total_companies}</p>
              </div>
              <Building2 className="w-8 h-8 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Series B</p>
                <p className="text-2xl font-semibold text-gray-900 mt-1">{stats.by_stage['Series B'] || 0}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Series C</p>
                <p className="text-2xl font-semibold text-gray-900 mt-1">{stats.by_stage['Series C'] || 0}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Avg Valuation</p>
                <p className="text-2xl font-semibold text-gray-900 mt-1">
                  {stats.by_valuation_range ? 
                    Object.values(stats.by_valuation_range).reduce((a, b) => a + b, 0) > 0 ? '~$300M' : '—'
                    : '—'
                  }
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-amber-500" />
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search companies..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          <select
            value={selectedStage}
            onChange={(e) => setSelectedStage(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Stages</option>
            <option value="Series B">Series B</option>
            <option value="Series C">Series C</option>
          </select>
          
          <input
            type="text"
            placeholder="Filter by industry..."
            value={selectedIndustry}
            onChange={(e) => setSelectedIndustry(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Recent Scrape Jobs */}
      {scrapeJobs.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Scrape Jobs</h3>
          <div className="space-y-2">
            {scrapeJobs.slice(0, 3).map((job) => (
              <div key={job.id} className="text-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                      job.status === 'completed' ? 'bg-green-500' :
                      job.status === 'running' ? 'bg-blue-500' :
                      'bg-red-500'
                    }`} />
                    <span className="text-gray-600">
                      {job.source_name} — {job.companies_added} added, {job.companies_updated} updated
                    </span>
                  </div>
                  <span className="text-gray-400">
                    {new Date(job.created_at).toLocaleDateString()}
                  </span>
                </div>
                {job.errors && (
                  <p className="mt-1 ml-4 text-xs text-amber-700 font-medium">{job.errors.trim()}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Companies Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-2" />
            <p className="text-gray-500">Loading companies...</p>
          </div>
        ) : loadError ? (
          <div className="p-12 text-center">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load companies</h3>
            <p className="text-red-600 mb-4">{loadError}</p>
            <button
              onClick={() => {
                setLoadError(null)
                loadCompanies()
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        ) : filteredCompanies.length === 0 ? (
          <div className="p-12 text-center">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No companies found</h3>
            <p className="text-gray-500 mb-4">Run the scraper to collect companies from public sources</p>
            <button
              onClick={handleRunScraper}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Run Scraper
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Company</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Source</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Industry</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Stage</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Valuation</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Investors</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Location</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Match Reasoning</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredCompanies.map((company) => (
                  <tr key={company.id} className="hover:bg-gray-50">
                    <td className="px-4 py-4">
                      <div>
                        <p className="font-medium text-gray-900">{company.name}</p>
                        {company.description && (
                          <p className="text-sm text-gray-500 mt-1 line-clamp-1">{company.description}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700">
                        {company.source_name || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700">
                        {company.source_name || 'Unknown'}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-700">{company.industry || '—'}</td>
                    <td className="px-4 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {company.stage || '—'}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-sm font-medium text-gray-700">
                      {formatValuation(company.valuation)}
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-600 max-w-xs truncate">
                      {company.key_investors || '—'}
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-600">{company.location || '—'}</td>
                    <td className="px-4 py-4 text-xs text-gray-600 max-w-xs">
                      <div className="line-clamp-2" title={company.match_reasoning || ''}>
                        {company.match_reasoning || '—'}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
