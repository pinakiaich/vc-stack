import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ChevronDown, ChevronRight, Building2, BarChart3, TrendingUp, Landmark, User, Swords, ExternalLink, FileDown, Share2, Plus, Loader2 } from 'lucide-react'
import { useAppStore } from '../store/appStore'
import { useDeals, useResearch } from '../hooks'
import type { FirmResult } from '../types'

// Mock firm data (fallback when no API data)
const mockFirmsData: Record<string, Partial<FirmResult> & { research: any }> = {
  '1': {
    id: '1',
    name: 'TechCorp AI',
    score: 92,
    industry: 'AI/ML',
    stage: 'Series A',
    location: 'San Francisco, CA',
    revenue: '$2.5M ARR',
    reason: 'Strong AI/ML team with proven B2B traction in the enterprise space. Recurring revenue model with 120% NDR demonstrates product-market fit.',
    research: {
      companyInfo: { name: 'TechCorp AI', country: 'United States', industry: 'AI/ML - Enterprise Software' },
      quantitativeData: { tam: '$45 Billion', sam: '$12 Billion', cagr: '32%', revenue: '$2.5M ARR', ndr: '120%', funding: '$8M Series A', valuation: '$25M', employees: '45' },
      industryBackground: 'The enterprise AI market is experiencing rapid growth, with TAM expected to reach $45B by 2027. Key drivers include increasing automation needs, improved ML model capabilities, and enterprise digital transformation initiatives. The B2B segment is particularly strong due to clear ROI metrics and growing IT budgets for AI initiatives.\n\nMajor trends include:\n• Shift from custom ML solutions to platform-based approaches\n• Growing demand for explainable AI in regulated industries\n• Integration of LLMs into enterprise workflows\n• Edge AI deployment for latency-sensitive applications',
      companyBackground: 'TechCorp AI was founded in 2021 by a team of ex-Google AI researchers. The company has developed a proprietary ML platform that enables enterprises to deploy AI models 10x faster than traditional approaches.\n\nKey milestones:\n• 2021: Founded, raised $2M seed\n• 2022: Launched platform, first 10 customers\n• 2023: Raised $8M Series A, expanded to 45 employees\n• 2024: 15 Fortune 500 customers, 200% YoY growth',
      founderProfile: 'CEO Jane Smith previously led the Google Brain team for 5 years, overseeing research that resulted in 20+ papers and 3 major product integrations. She holds a PhD in Machine Learning from Stanford.\n\nCTO John Doe was a founding engineer at OpenAI, where he led the infrastructure team. He previously worked at Tesla Autopilot.\n\nThe founding team has:\n• 3 successful exits between them\n• 50+ years combined ML experience\n• Strong network in enterprise software',
      competition: 'Main competitors include:\n\n1. DataRobot - Established player, $6B+ valuation, broader but less specialized\n2. H2O.ai - Open source focus, strong in financial services\n3. AWS SageMaker - Cloud-native, bundled with AWS ecosystem\n\nTechCorp differentiates through:\n• 10x faster deployment (proprietary AutoML)\n• Enterprise-grade security (SOC2, HIPAA compliant)\n• Hybrid cloud support (unlike pure SaaS competitors)\n• Superior customer success (120% NDR vs industry avg 105%)',
    }
  },
  '2': {
    id: '2', name: 'DataFlow Inc', score: 85, industry: 'Data Infrastructure', stage: 'Series A', location: 'New York, NY', revenue: '$1.8M ARR',
    reason: 'Data infrastructure play with enterprise focus. Strong technical founders from Google and Meta.',
    research: {
      companyInfo: { name: 'DataFlow Inc', country: 'United States', industry: 'Data Infrastructure' },
      quantitativeData: { tam: '$35 Billion', sam: '$8 Billion', cagr: '28%', revenue: '$1.8M ARR', ndr: '115%', funding: '$6M Series A', valuation: '$18M', employees: '32' },
      industryBackground: 'The data infrastructure market continues to grow rapidly as enterprises struggle with increasing data volumes and real-time processing needs.',
      companyBackground: 'DataFlow was founded in 2022 by former Google and Meta data engineers who saw the need for better real-time data pipelines.',
      founderProfile: 'Strong technical founding team with deep experience in distributed systems at scale.',
      competition: 'Competes with Confluent, Databricks, and Snowflake in adjacent spaces.',
    }
  }
}

interface AccordionSectionProps {
  id: string
  icon: React.ReactNode
  title: string
  content: string
  defaultOpen?: boolean
  loading?: boolean
}

function AccordionSection({ id, icon, title, content, defaultOpen = false, loading = false }: AccordionSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center space-x-3">
          {icon}
          <span className="font-medium text-gray-900">{title}</span>
        </div>
        {loading ? (
          <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
        ) : isOpen ? (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-400" />
        )}
      </button>
      {isOpen && (
        <div className="px-4 py-4 bg-white">
          {loading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-full"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
          ) : (
            <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">{content || 'No data available'}</p>
          )}
        </div>
      )}
    </div>
  )
}

function ScoreRing({ score, label, color }: { score: number; label: string; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-500">{label}</span>
        <span className={`font-semibold ${color}`}>{score}%</span>
      </div>
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all ${
            score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-blue-500' : 'bg-amber-500'
          }`} 
          style={{ width: `${score}%` }} 
        />
      </div>
    </div>
  )
}

export function MemoViewPage() {
  const { id } = useParams()
  const { state } = useAppStore()
  const { createDeal } = useDeals()
  const [creatingDeal, setCreatingDeal] = useState(false)
  
  // Find firm from filter results or use mock data
  const firmFromResults = state.filterResults.find(f => f.id === id)
  const mockFirm = mockFirmsData[id || '1']
  
  const firm = firmFromResults || {
    id: mockFirm?.id || '0',
    name: mockFirm?.name || 'Unknown Firm',
    score: mockFirm?.score || 0,
    industry: mockFirm?.industry || 'N/A',
    stage: mockFirm?.stage || 'N/A',
    location: mockFirm?.location || 'N/A',
    revenue: mockFirm?.revenue || 'N/A',
    reason: mockFirm?.reason || 'No data available',
    rank: 0,
  }
  
  const research = mockFirm?.research || {
    companyInfo: { name: firm.name, country: 'N/A', industry: firm.industry },
    quantitativeData: {},
    industryBackground: 'Research data not available.',
    companyBackground: 'Research data not available.',
    founderProfile: 'Research data not available.',
    competition: 'Research data not available.',
  }

  const handleCreateDeal = async () => {
    setCreatingDeal(true)
    try {
      await createDeal({
        name: firm.name,
        sector: firm.industry,
        stage: firm.stage,
        source: 'memo_view',
        status: 'active',
      })
      // Show success (could add toast notification)
    } catch (err) {
      console.error('Failed to create deal:', err)
    } finally {
      setCreatingDeal(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Back Link */}
      <Link to="/results" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 transition-colors">
        <ArrowLeft className="w-4 h-4 mr-1" />
        Back to Results
      </Link>

      {/* Firm Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">{firm.name}</h1>
            <div className="flex flex-wrap items-center gap-2 mt-3">
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                🏷️ {firm.industry}
              </span>
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {firm.stage}
              </span>
              {firm.location && firm.location !== 'N/A' && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  📍 {firm.location}
                </span>
              )}
              {firm.revenue && firm.revenue !== 'N/A' && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  💰 {firm.revenue}
                </span>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Match Score</div>
            <div className={`text-3xl font-bold ${
              firm.score >= 80 ? 'text-green-600' : firm.score >= 60 ? 'text-blue-600' : 'text-amber-600'
            }`}>
              {firm.score}%
            </div>
          </div>
        </div>
        
        <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
          <div className="text-sm font-medium text-blue-700 mb-1">Match Reason:</div>
          <p className="text-blue-600">{firm.reason}</p>
        </div>
      </div>

      {/* Main Content + Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Memo Content */}
        <div className="lg:col-span-2 space-y-4">
          {/* Company Information */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center space-x-3 mb-4">
              <Building2 className="w-5 h-5 text-gray-400" />
              <h2 className="text-lg font-medium text-gray-900">Company Information</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">Company Name</div>
                <div className="font-medium text-gray-900">{research.companyInfo.name}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Country</div>
                <div className="font-medium text-gray-900">{research.companyInfo.country}</div>
              </div>
              <div className="md:col-span-2">
                <div className="text-sm text-gray-500">Industry</div>
                <div className="font-medium text-gray-900">{research.companyInfo.industry}</div>
              </div>
            </div>
          </div>

          {/* Quantitative Data */}
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <div className="flex items-center space-x-3 mb-4">
              <BarChart3 className="w-5 h-5 text-gray-400" />
              <h2 className="text-lg font-medium text-gray-900">Quantitative Data</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Market Size</h3>
                <div className="grid grid-cols-2 gap-3">
                  {research.quantitativeData.tam && (
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="text-xs text-gray-500 mb-1">TAM</div>
                      <div className="text-lg font-semibold text-gray-900">{research.quantitativeData.tam}</div>
                    </div>
                  )}
                  {research.quantitativeData.sam && (
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="text-xs text-gray-500 mb-1">SAM</div>
                      <div className="text-lg font-semibold text-gray-900">{research.quantitativeData.sam}</div>
                    </div>
                  )}
                  {research.quantitativeData.cagr && (
                    <div className="p-3 bg-gray-50 rounded-lg col-span-2">
                      <div className="text-xs text-gray-500 mb-1">Market Growth (CAGR)</div>
                      <div className="text-lg font-semibold text-green-600">{research.quantitativeData.cagr}</div>
                    </div>
                  )}
                </div>
              </div>
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Company Metrics</h3>
                <div className="grid grid-cols-2 gap-3">
                  {research.quantitativeData.revenue && (
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="text-xs text-gray-500 mb-1">Revenue</div>
                      <div className="text-lg font-semibold text-gray-900">{research.quantitativeData.revenue}</div>
                    </div>
                  )}
                  {research.quantitativeData.ndr && (
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="text-xs text-gray-500 mb-1">NDR</div>
                      <div className="text-lg font-semibold text-green-600">{research.quantitativeData.ndr}</div>
                    </div>
                  )}
                  {research.quantitativeData.funding && (
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="text-xs text-gray-500 mb-1">Funding</div>
                      <div className="text-lg font-semibold text-gray-900">{research.quantitativeData.funding}</div>
                    </div>
                  )}
                  {research.quantitativeData.valuation && (
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className="text-xs text-gray-500 mb-1">Valuation</div>
                      <div className="text-lg font-semibold text-gray-900">{research.quantitativeData.valuation}</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Accordion Sections */}
          <AccordionSection
            id="industry"
            icon={<TrendingUp className="w-5 h-5 text-gray-400" />}
            title="Industry Background & Growth"
            content={research.industryBackground}
            defaultOpen={true}
          />
          
          <AccordionSection
            id="company"
            icon={<Landmark className="w-5 h-5 text-gray-400" />}
            title="Company Background"
            content={research.companyBackground}
          />
          
          <AccordionSection
            id="founder"
            icon={<User className="w-5 h-5 text-gray-400" />}
            title="Founder Profile"
            content={research.founderProfile}
          />
          
          <AccordionSection
            id="competition"
            icon={<Swords className="w-5 h-5 text-gray-400" />}
            title="Competition & Market Landscape"
            content={research.competition}
          />
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Quick Stats */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">📊 Quick Stats</h3>
            <div className="space-y-3 text-sm">
              {research.quantitativeData.revenue && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Revenue</span>
                  <span className="font-medium text-gray-900">{research.quantitativeData.revenue}</span>
                </div>
              )}
              {research.quantitativeData.employees && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Employees</span>
                  <span className="font-medium text-gray-900">{research.quantitativeData.employees}</span>
                </div>
              )}
              {research.quantitativeData.funding && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Funding</span>
                  <span className="font-medium text-gray-900">{research.quantitativeData.funding}</span>
                </div>
              )}
              {research.quantitativeData.valuation && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Valuation</span>
                  <span className="font-medium text-gray-900">{research.quantitativeData.valuation}</span>
                </div>
              )}
            </div>
          </div>

          {/* Scores */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">📈 Scores</h3>
            <div className="space-y-4">
              <ScoreRing score={firm.score} label="Match Score" color="text-green-600" />
              <ScoreRing score={85} label="Opportunity" color="text-blue-600" />
              <ScoreRing score={72} label="Exit Probability" color="text-purple-600" />
            </div>
          </div>

          {/* Links */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">🔗 Links</h3>
            <div className="space-y-2">
              <a href="#" className="flex items-center text-sm text-blue-600 hover:text-blue-700 transition-colors">
                <ExternalLink className="w-4 h-4 mr-2" />
                Website
              </a>
              <a href="#" className="flex items-center text-sm text-blue-600 hover:text-blue-700 transition-colors">
                <ExternalLink className="w-4 h-4 mr-2" />
                Crunchbase
              </a>
              <a href="#" className="flex items-center text-sm text-blue-600 hover:text-blue-700 transition-colors">
                <ExternalLink className="w-4 h-4 mr-2" />
                LinkedIn
              </a>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">📝 Actions</h3>
            <div className="space-y-2">
              <button 
                onClick={handleCreateDeal}
                disabled={creatingDeal}
                className="w-full flex items-center justify-center px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-sm transition-colors disabled:opacity-50"
              >
                {creatingDeal ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4 mr-2" />
                )}
                Create Deal
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 text-sm transition-colors">
                <FileDown className="w-4 h-4 mr-2" />
                Export PDF
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 text-sm transition-colors">
                <Share2 className="w-4 h-4 mr-2" />
                Share
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
