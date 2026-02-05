import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, Filter, ChevronRight, AlertCircle } from 'lucide-react'
import { useAppStore } from '../store/appStore'
import { useDeals } from '../hooks'
import type { FirmResult, DealCreate } from '../types'

function ScoreBar({ score }: { score: number }) {
  const getColor = (score: number) => {
    if (score >= 90) return 'bg-green-500'
    if (score >= 75) return 'bg-green-400'
    if (score >= 50) return 'bg-amber-500'
    return 'bg-red-500'
  }

  const getTextColor = (score: number) => {
    if (score >= 90) return 'text-green-700'
    if (score >= 75) return 'text-green-600'
    if (score >= 50) return 'text-amber-600'
    return 'text-red-600'
  }

  return (
    <div className="flex items-center space-x-2">
      <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={`h-full ${getColor(score)} rounded-full transition-all`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={`text-sm font-semibold ${getTextColor(score)}`}>{score}%</span>
    </div>
  )
}

function IndustryBadge({ industry }: { industry: string }) {
  const colors: Record<string, string> = {
    'AI/ML': 'bg-purple-100 text-purple-800',
    'Data Infrastructure': 'bg-blue-100 text-blue-800',
    'Cybersecurity': 'bg-red-100 text-red-800',
    'ML Ops': 'bg-indigo-100 text-indigo-800',
    'FinTech': 'bg-green-100 text-green-800',
    'HealthTech': 'bg-pink-100 text-pink-800',
    'Autonomous': 'bg-orange-100 text-orange-800',
    'Robotics': 'bg-cyan-100 text-cyan-800',
    'Infrastructure': 'bg-gray-100 text-gray-800',
  }
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[industry] || 'bg-gray-100 text-gray-800'}`}>
      {industry}
    </span>
  )
}

function StageBadge({ stage }: { stage: string }) {
  const colors: Record<string, string> = {
    'Seed': 'bg-emerald-100 text-emerald-800',
    'Series A': 'bg-blue-100 text-blue-800',
    'Series B': 'bg-violet-100 text-violet-800',
    'Series C': 'bg-amber-100 text-amber-800',
  }
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[stage] || 'bg-gray-100 text-gray-800'}`}>
      {stage}
    </span>
  )
}

export function ResultsListPage() {
  const navigate = useNavigate()
  const { state } = useAppStore()
  const { createDeal } = useDeals()
  
  const results = state.filterResults
  const metadata = state.filterMetadata

  // Handle creating a deal from a firm result
  const handleCreateDeal = async (firm: FirmResult) => {
    const dealData: DealCreate = {
      name: firm.name,
      sector: firm.industry,
      stage: firm.stage,
      source: 'filter_results',
      status: 'active',
    }
    
    const deal = await createDeal(dealData)
    if (deal) {
      // Navigate to memo view with deal context
      navigate(`/memo/${firm.id}`)
    }
  }

  // Empty state
  if (results.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <Link to="/" className="flex items-center text-sm text-gray-500 hover:text-gray-700 mb-2">
            <ArrowLeft className="w-4 h-4 mr-1" />
            Run Setup
          </Link>
          <h1 className="text-2xl font-semibold text-gray-900">Results</h1>
        </div>
        
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-gray-400" />
          </div>
          <h2 className="text-lg font-medium text-gray-900 mb-2">No results yet</h2>
          <p className="text-gray-500 mb-6">Run a filter to see matching firms here</p>
          <Link 
            to="/"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            Go to Run Setup
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link to="/" className="flex items-center text-sm text-gray-500 hover:text-gray-700 mb-2">
            <ArrowLeft className="w-4 h-4 mr-1" />
            New Run
          </Link>
          <h1 className="text-2xl font-semibold text-gray-900">Results</h1>
          <p className="text-gray-500">Showing top {results.length} firms matching your criteria</p>
        </div>
        
        <div className="flex space-x-3">
          <button className="flex items-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </button>
          <button className="flex items-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Criteria Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <div>
            <span className="text-sm font-medium text-blue-700">🎯 Criteria:</span>
            <span className="ml-2 text-blue-600">"{state.criteria}"</span>
          </div>
          {metadata && (
            <div className="flex items-center space-x-4 text-sm text-blue-600">
              <span>📊 Processed {metadata.totalProcessed} firms in {(metadata.processingTimeMs / 1000).toFixed(1)}s</span>
              {metadata.cacheHitRate > 0 && (
                <span>💾 Cache: {Math.round(metadata.cacheHitRate * 100)}% hit rate</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-12">#</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider min-w-[200px]">Firm Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-32">Score</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-32">Industry</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-24">Stage</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-28">Valuation</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider min-w-[150px]">Key Investors</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-12"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {results.map((firm) => (
                <tr key={firm.id} className="hover:bg-gray-50 transition-colors group">
                  <td className="px-4 py-4">
                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-semibold ${
                      firm.rank <= 3 
                        ? 'bg-amber-100 text-amber-700' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {firm.rank}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <Link to={`/memo/${firm.id}`} className="block group-hover:bg-transparent">
                      <span className="text-blue-600 font-medium hover:text-blue-700 hover:underline">
                        📌 {firm.name}
                      </span>
                      <p className="text-sm text-gray-500 mt-1 line-clamp-2 max-w-md">{firm.reason}</p>
                    </Link>
                  </td>
                  <td className="px-4 py-4">
                    <ScoreBar score={firm.score} />
                  </td>
                  <td className="px-4 py-4">
                    <IndustryBadge industry={firm.industry} />
                  </td>
                  <td className="px-4 py-4">
                    <StageBadge stage={firm.stage} />
                  </td>
                  <td className="px-4 py-4">
                    <span className="text-sm text-gray-700 font-medium">
                      {firm.valuation || '—'}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <span className="text-sm text-gray-600 line-clamp-2" title={firm.keyInvestors || ''}>
                      {firm.keyInvestors || '—'}
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <Link 
                      to={`/memo/${firm.id}`}
                      className="text-gray-400 hover:text-blue-600 transition-colors"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Help Text */}
      <p className="text-center text-sm text-gray-500">
        💡 Click on any firm name to view detailed investment memo
      </p>
    </div>
  )
}
