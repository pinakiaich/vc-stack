# VC Firm Filter - UI Handover & Launch Guide

**Version:** 1.0  
**Date:** January 22, 2026  
**For:** Development Team

---

## Quick Start (5 minutes)

### Prerequisites Check

```bash
# Check Node.js (need v18+)
node --version

# Check npm or pnpm
npm --version
# or
pnpm --version
```

If not installed:
```bash
# macOS with Homebrew
brew install node

# Or use nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

---

## Option A: Scaffold New React Project (Recommended)

### Step 1: Create Project

```bash
# Navigate to vc-stack directory
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"

# Create new React app with Vite + TypeScript
npm create vite@latest vc-filter-ui -- --template react-ts

# Enter the new directory
cd vc-filter-ui

# Install dependencies
npm install
```

### Step 2: Install UI Dependencies

```bash
# Core UI libraries
npm install @radix-ui/react-accordion @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tooltip @radix-ui/react-checkbox @radix-ui/react-select @radix-ui/react-tabs

# Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# TanStack Table for DataGrid
npm install @tanstack/react-table

# React Query for API calls
npm install @tanstack/react-query

# React Router
npm install react-router-dom

# Form handling
npm install react-hook-form zod @hookform/resolvers

# File upload
npm install react-dropzone

# Icons
npm install lucide-react

# Utilities
npm install clsx tailwind-merge class-variance-authority
```

### Step 3: Configure Tailwind

Replace `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        score: {
          excellent: '#10b981',
          good: '#22c55e',
          moderate: '#f59e0b',
          low: '#ef4444',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
```

Replace `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  /* Design tokens from UI_SPEC_PRODUCTION.md */
  --color-surface-primary: #ffffff;
  --color-surface-secondary: #f9fafb;
  --color-border-default: #e5e7eb;
  --shadow-focus: 0 0 0 3px #bfdbfe;
}

body {
  font-family: 'Inter', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}
```

### Step 4: Create Basic App Structure

Create `src/App.tsx`:

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppShell } from './components/layout/AppShell'
import { RunSetupPage } from './pages/RunSetupPage'
import { ResultsListPage } from './pages/ResultsListPage'
import { MemoViewPage } from './pages/MemoViewPage'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<RunSetupPage />} />
            <Route path="/results" element={<ResultsListPage />} />
            <Route path="/memo/:id" element={<MemoViewPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
```

Create `src/components/layout/AppShell.tsx`:

```tsx
import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Upload, List, FileText } from 'lucide-react'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const location = useLocation()
  
  const navItems = [
    { id: 'run-setup', label: 'Run Setup', icon: Upload, href: '/' },
    { id: 'results', label: 'Results', icon: List, href: '/results' },
    { id: 'memo', label: 'Memo', icon: FileText, href: '/memo' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center space-x-2">
              <span className="text-2xl">🎯</span>
              <span className="font-semibold text-gray-900">VC Firm Filter</span>
            </div>
            
            {/* Navigation */}
            <nav className="flex space-x-1">
              {navItems.map((item) => {
                const isActive = location.pathname === item.href || 
                  (item.href !== '/' && location.pathname.startsWith(item.href))
                return (
                  <Link
                    key={item.id}
                    to={item.href}
                    className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive 
                        ? 'bg-primary-50 text-primary-700' 
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <item.icon className="w-4 h-4 mr-2" />
                    {item.label}
                  </Link>
                )
              })}
            </nav>
            
            {/* User Menu Placeholder */}
            <div className="w-8 h-8 bg-gray-200 rounded-full" />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Status Bar */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 py-2 px-4">
        <div className="max-w-7xl mx-auto flex items-center space-x-4 text-xs text-gray-500">
          <span className="flex items-center">
            <span className="w-2 h-2 bg-green-500 rounded-full mr-1.5"></span>
            API Connected
          </span>
          <span>Cache: 65% hit rate</span>
          <span>RAG: 1,234 chunks</span>
        </div>
      </footer>
    </div>
  )
}
```

Create `src/pages/RunSetupPage.tsx`:

```tsx
import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileSpreadsheet, Key, Search, Brain, BookOpen } from 'lucide-react'

export function RunSetupPage() {
  const [file, setFile] = useState<File | null>(null)
  const [criteria, setCriteria] = useState('')
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
  })

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Run Setup</h1>
        <p className="mt-1 text-gray-500">Upload your firm data and configure filtering criteria</p>
      </div>

      {/* Step 1: File Upload */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
            <Upload className="w-4 h-4 text-primary-600" />
          </div>
          <h2 className="text-lg font-medium text-gray-900">Step 1: Upload Excel File</h2>
        </div>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive 
              ? 'border-primary-500 bg-primary-50' 
              : file 
                ? 'border-green-300 bg-green-50' 
                : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          
          {file ? (
            <div className="flex flex-col items-center">
              <FileSpreadsheet className="w-12 h-12 text-green-500 mb-3" />
              <p className="font-medium text-gray-900">{file.name}</p>
              <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
              <button 
                onClick={(e) => { e.stopPropagation(); setFile(null) }}
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
      </div>

      {/* Step 2: API Key */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
            <Key className="w-4 h-4 text-primary-600" />
          </div>
          <h2 className="text-lg font-medium text-gray-900">Step 2: Configure API Key</h2>
        </div>

        {apiKeyConfigured ? (
          <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <span className="text-green-600">✅</span>
              <span className="text-green-700 font-medium">API Key configured</span>
              <span className="text-gray-500 text-sm">sk-•••••••••••••1234</span>
            </div>
            <button 
              onClick={() => setApiKeyConfigured(false)}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Change
            </button>
          </div>
        ) : (
          <div className="flex space-x-3">
            <input
              type="password"
              placeholder="sk-..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <button 
              onClick={() => setApiKeyConfigured(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium"
            >
              Save Key
            </button>
          </div>
        )}
      </div>

      {/* Step 3: Criteria */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
            <Search className="w-4 h-4 text-primary-600" />
          </div>
          <h2 className="text-lg font-medium text-gray-900">Step 3: Enter Filtering Criteria</h2>
        </div>

        <textarea
          value={criteria}
          onChange={(e) => setCriteria(e.target.value)}
          placeholder="e.g., Looking for AI/ML startups with revenue >$1M, Series A stage, B2B focus, strong technical team"
          className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
        />
        <p className="mt-2 text-sm text-gray-500">
          💡 Tip: Be specific about industry, stage, revenue metrics, and team characteristics
        </p>
      </div>

      {/* Step 4: Optional */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
            <Brain className="w-4 h-4 text-gray-600" />
          </div>
          <h2 className="text-lg font-medium text-gray-900">Step 4: Optional Enhancements</h2>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <BookOpen className="w-5 h-5 text-gray-400" />
              <span className="font-medium text-gray-700">RAG Documents</span>
            </div>
            <p className="text-sm text-gray-500">0 documents loaded</p>
            <button className="mt-2 text-sm text-primary-600 hover:text-primary-700">
              + Add documents
            </button>
          </div>
          
          <div className="p-4 border border-gray-200 rounded-lg">
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
          disabled={!file || !criteria}
          className={`px-8 py-3 rounded-lg font-medium text-lg transition-colors ${
            file && criteria
              ? 'bg-primary-600 text-white hover:bg-primary-700'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          🔍 Filter Top 10 Firms
        </button>
        <p className="mt-2 text-sm text-gray-500">Estimated time: ~30 seconds</p>
      </div>
    </div>
  )
}
```

Create `src/pages/ResultsListPage.tsx`:

```tsx
import { Link } from 'react-router-dom'
import { ArrowLeft, Download, Filter } from 'lucide-react'

// Mock data for demo
const mockResults = [
  { id: '1', rank: 1, name: 'TechCorp AI', score: 92, industry: 'AI/ML', stage: 'Series A', reason: 'Strong AI/ML team with proven B2B traction in the enterprise space. Recurring revenue model with 120% NDR.' },
  { id: '2', rank: 2, name: 'DataFlow Inc', score: 85, industry: 'Data Infrastructure', stage: 'Series A', reason: 'Data infrastructure play with enterprise focus. Strong technical founders from Google and Meta.' },
  { id: '3', rank: 3, name: 'CloudSecure', score: 78, industry: 'Cybersecurity', stage: 'Series B', reason: 'Cybersecurity with AI-powered threat detection. Growing 3x YoY in enterprise segment.' },
  { id: '4', rank: 4, name: 'MLOps Pro', score: 72, industry: 'ML Ops', stage: 'Series A', reason: 'MLOps platform with strong developer adoption. 500+ enterprise customers.' },
  { id: '5', rank: 5, name: 'NeuralNet Co', score: 68, industry: 'AI/ML', stage: 'Seed', reason: 'Early stage but promising neural network technology. Founded by Stanford AI lab researchers.' },
]

function ScoreBar({ score }: { score: number }) {
  const getColor = (score: number) => {
    if (score >= 90) return 'bg-green-500'
    if (score >= 75) return 'bg-green-400'
    if (score >= 50) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="flex items-center space-x-2">
      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div 
          className={`h-full ${getColor(score)} rounded-full`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-sm font-medium text-gray-700">{score}%</span>
    </div>
  )
}

export function ResultsListPage() {
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
          <p className="text-gray-500">Showing 10 firms matching your criteria</p>
        </div>
        
        <div className="flex space-x-3">
          <button className="flex items-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </button>
          <button className="flex items-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Criteria Banner */}
      <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-sm font-medium text-primary-700">🎯 Criteria:</span>
            <span className="ml-2 text-primary-600">"AI/ML startups, Series A, B2B, revenue &gt;$1M"</span>
          </div>
          <div className="flex items-center space-x-4 text-sm text-primary-600">
            <span>📊 Processed 247 firms in 28.3s</span>
            <span>💾 Cache: 65% hit rate</span>
          </div>
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-16">#</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Firm Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-36">Score</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Industry</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28">Stage</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {mockResults.map((firm) => (
              <tr key={firm.id} className="hover:bg-gray-50 cursor-pointer">
                <td className="px-4 py-4">
                  <span className="inline-flex items-center justify-center w-6 h-6 bg-primary-100 text-primary-700 rounded-full text-sm font-medium">
                    {firm.rank}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <Link to={`/memo/${firm.id}`} className="block">
                    <span className="text-primary-600 font-medium hover:text-primary-700">
                      📌 {firm.name}
                    </span>
                    <p className="text-sm text-gray-500 mt-1 line-clamp-2">{firm.reason}</p>
                  </Link>
                </td>
                <td className="px-4 py-4">
                  <ScoreBar score={firm.score} />
                </td>
                <td className="px-4 py-4">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {firm.industry}
                  </span>
                </td>
                <td className="px-4 py-4">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                    {firm.stage}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Help Text */}
      <p className="text-center text-sm text-gray-500">
        💡 Click on any firm name to view detailed investment memo
      </p>
    </div>
  )
}
```

Create `src/pages/MemoViewPage.tsx`:

```tsx
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, ChevronDown, ChevronRight, Building2, BarChart3, TrendingUp, Landmark, User, Swords, ExternalLink, FileDown, Share2 } from 'lucide-react'

// Mock data
const mockFirm = {
  id: '1',
  name: 'TechCorp AI',
  score: 92,
  industry: 'AI/ML',
  stage: 'Series A',
  location: 'San Francisco, CA',
  revenue: '$2.5M ARR',
  reason: 'Strong AI/ML team with proven B2B traction in the enterprise space. Recurring revenue model with 120% NDR demonstrates product-market fit.',
  research: {
    companyInfo: {
      name: 'TechCorp AI',
      country: 'United States',
      industry: 'AI/ML - Enterprise Software',
    },
    quantitativeData: {
      tam: '$45 Billion',
      sam: '$12 Billion',
      cagr: '32%',
      revenue: '$2.5M ARR',
      ndr: '120%',
      funding: '$8M Series A',
      valuation: '$25M',
      employees: '45',
    },
    industryBackground: 'The enterprise AI market is experiencing rapid growth, with TAM expected to reach $45B by 2027. Key drivers include increasing automation needs, improved ML model capabilities, and enterprise digital transformation initiatives. The B2B segment is particularly strong due to clear ROI metrics and growing IT budgets for AI initiatives.',
    companyBackground: 'TechCorp AI was founded in 2021 by a team of ex-Google AI researchers. The company has developed a proprietary ML platform that enables enterprises to deploy AI models 10x faster than traditional approaches. They have secured contracts with 15 Fortune 500 companies and are growing revenue at 200% YoY.',
    founderProfile: 'CEO Jane Smith previously led the Google Brain team for 5 years. CTO John Doe was a founding engineer at OpenAI. The founding team has 3 successful exits between them and deep expertise in enterprise ML.',
    competition: 'Main competitors include DataRobot, H2O.ai, and AWS SageMaker. TechCorp differentiates through its focus on deployment speed and enterprise-grade security. Competitive moat includes proprietary technology and strong enterprise relationships.',
  }
}

interface AccordionSectionProps {
  id: string
  icon: React.ReactNode
  title: string
  content: string
  defaultOpen?: boolean
}

function AccordionSection({ id, icon, title, content, defaultOpen = false }: AccordionSectionProps) {
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
        {isOpen ? (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-400" />
        )}
      </button>
      {isOpen && (
        <div className="px-4 py-4 bg-white">
          <p className="text-gray-700 whitespace-pre-wrap">{content}</p>
        </div>
      )}
    </div>
  )
}

export function MemoViewPage() {
  const { id } = useParams()
  const firm = mockFirm // In production, fetch by id

  return (
    <div className="space-y-6">
      {/* Back Link */}
      <Link to="/results" className="flex items-center text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="w-4 h-4 mr-1" />
        Back to Results
      </Link>

      {/* Firm Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">{firm.name}</h1>
            <div className="flex items-center space-x-3 mt-3">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                🏷️ {firm.industry}
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                {firm.stage}
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                📍 {firm.location}
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                💰 {firm.revenue}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-500">Match Score</div>
            <div className="text-3xl font-bold text-green-600">{firm.score}%</div>
          </div>
        </div>
        
        <div className="mt-4 p-4 bg-primary-50 rounded-lg">
          <div className="text-sm font-medium text-primary-700 mb-1">Match Reason:</div>
          <p className="text-primary-600">{firm.reason}</p>
        </div>
      </div>

      {/* Main Content + Sidebar */}
      <div className="grid grid-cols-3 gap-6">
        {/* Memo Content */}
        <div className="col-span-2 space-y-4">
          {/* Company Information */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <Building2 className="w-5 h-5 text-gray-400" />
              <h2 className="text-lg font-medium text-gray-900">Company Information</h2>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">Company Name</div>
                <div className="font-medium text-gray-900">{firm.research.companyInfo.name}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Country</div>
                <div className="font-medium text-gray-900">{firm.research.companyInfo.country}</div>
              </div>
              <div className="col-span-2">
                <div className="text-sm text-gray-500">Industry</div>
                <div className="font-medium text-gray-900">{firm.research.companyInfo.industry}</div>
              </div>
            </div>
          </div>

          {/* Quantitative Data */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <BarChart3 className="w-5 h-5 text-gray-400" />
              <h2 className="text-lg font-medium text-gray-900">Quantitative Data</h2>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-700 uppercase tracking-wider">Market Size</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500">TAM</div>
                    <div className="text-lg font-semibold text-gray-900">{firm.research.quantitativeData.tam}</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500">SAM</div>
                    <div className="text-lg font-semibold text-gray-900">{firm.research.quantitativeData.sam}</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500">CAGR</div>
                    <div className="text-lg font-semibold text-green-600">{firm.research.quantitativeData.cagr}</div>
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-700 uppercase tracking-wider">Company Metrics</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500">Revenue</div>
                    <div className="text-lg font-semibold text-gray-900">{firm.research.quantitativeData.revenue}</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500">NDR</div>
                    <div className="text-lg font-semibold text-green-600">{firm.research.quantitativeData.ndr}</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500">Funding</div>
                    <div className="text-lg font-semibold text-gray-900">{firm.research.quantitativeData.funding}</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-xs text-gray-500">Valuation</div>
                    <div className="text-lg font-semibold text-gray-900">{firm.research.quantitativeData.valuation}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Accordion Sections */}
          <AccordionSection
            id="industry"
            icon={<TrendingUp className="w-5 h-5 text-gray-400" />}
            title="Industry Background & Growth"
            content={firm.research.industryBackground}
          />
          
          <AccordionSection
            id="company"
            icon={<Landmark className="w-5 h-5 text-gray-400" />}
            title="Company Background"
            content={firm.research.companyBackground}
          />
          
          <AccordionSection
            id="founder"
            icon={<User className="w-5 h-5 text-gray-400" />}
            title="Founder Profile"
            content={firm.research.founderProfile}
          />
          
          <AccordionSection
            id="competition"
            icon={<Swords className="w-5 h-5 text-gray-400" />}
            title="Competition & Market Landscape"
            content={firm.research.competition}
          />
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Quick Stats */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">📊 Quick Stats</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Revenue</span>
                <span className="font-medium">{firm.research.quantitativeData.revenue}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Employees</span>
                <span className="font-medium">{firm.research.quantitativeData.employees}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Funding</span>
                <span className="font-medium">{firm.research.quantitativeData.funding}</span>
              </div>
            </div>
          </div>

          {/* Scores */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">📈 Scores</h3>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Match Score</span>
                  <span className="font-medium text-green-600">{firm.score}%</span>
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full">
                  <div className="h-full bg-green-500 rounded-full" style={{ width: `${firm.score}%` }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Opportunity</span>
                  <span className="font-medium text-blue-600">85%</span>
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: '85%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Exit Probability</span>
                  <span className="font-medium text-purple-600">72%</span>
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full">
                  <div className="h-full bg-purple-500 rounded-full" style={{ width: '72%' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Links */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">🔗 Links</h3>
            <div className="space-y-2">
              <a href="#" className="flex items-center text-sm text-primary-600 hover:text-primary-700">
                <ExternalLink className="w-4 h-4 mr-2" />
                Website
              </a>
              <a href="#" className="flex items-center text-sm text-primary-600 hover:text-primary-700">
                <ExternalLink className="w-4 h-4 mr-2" />
                Crunchbase
              </a>
              <a href="#" className="flex items-center text-sm text-primary-600 hover:text-primary-700">
                <ExternalLink className="w-4 h-4 mr-2" />
                LinkedIn
              </a>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-white rounded-xl border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-3">📝 Actions</h3>
            <div className="space-y-2">
              <button className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium text-sm">
                Create Deal
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 text-sm">
                <FileDown className="w-4 h-4 mr-2" />
                Export PDF
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 text-sm">
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
```

### Step 5: Launch the UI

```bash
# Make sure you're in the vc-filter-ui directory
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/vc-filter-ui"

# Start development server
npm run dev
```

The app will be available at **http://localhost:5173**

---

## Option B: Quick Preview with Existing Streamlit (Current)

If you want to keep using the existing prototype while the production UI is being built:

```bash
# Navigate to vc-stack directory
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"

# Install dependencies if not already installed
pip install streamlit pandas openpyxl openai

# Run Streamlit app
streamlit run streamlit_app.py
```

The Streamlit app will be available at **http://localhost:8501**

---

## Verification Checklist

After launching, verify the following:

### Run Setup Page (`/`)
- [ ] Page loads without errors
- [ ] File drop zone is visible
- [ ] Can drag & drop Excel file
- [ ] Can click to browse files
- [ ] File preview shows after upload
- [ ] API key input works
- [ ] Criteria textarea accepts input
- [ ] "Filter Top 10 Firms" button enables when ready

### Results List Page (`/results`)
- [ ] Page loads with results table
- [ ] Firm names are clickable links
- [ ] Score bars display correctly
- [ ] Industry/Stage badges show
- [ ] Navigation back to Run Setup works

### Memo View Page (`/memo/:id`)
- [ ] Page loads with firm header
- [ ] Score displays prominently
- [ ] Badges show (industry, stage, location)
- [ ] Company Information section visible
- [ ] Quantitative Data grid displays
- [ ] Accordion sections expand/collapse
- [ ] Sidebar shows Quick Stats, Scores, Links, Actions
- [ ] Back to Results link works

---

## Connecting to Existing Backend

To connect the new UI to your existing Python backend:

### 1. Start the FastAPI Backend

```bash
# In a separate terminal
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack/backend"
uvicorn app.main:app --reload --port 8000
```

### 2. Configure API Client

Create `src/lib/api/client.ts`:

```typescript
const API_BASE_URL = 'http://localhost:8000'

export async function filterFirms(criteria: string, fileData: File) {
  const formData = new FormData()
  formData.append('file', fileData)
  formData.append('criteria', criteria)
  
  const response = await fetch(`${API_BASE_URL}/filter`, {
    method: 'POST',
    body: formData,
  })
  
  if (!response.ok) throw new Error('Failed to filter firms')
  return response.json()
}

export async function getFirmResearch(firmId: string) {
  const response = await fetch(`${API_BASE_URL}/v2/deals/${firmId}/research-findings`)
  if (!response.ok) throw new Error('Failed to fetch research')
  return response.json()
}
```

### 3. Enable CORS on Backend

In your FastAPI `main.py`, ensure CORS is enabled:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Troubleshooting

### Issue: `npm create vite` fails
```bash
# Clear npm cache
npm cache clean --force

# Try with npx
npx create-vite@latest vc-filter-ui --template react-ts
```

### Issue: Tailwind classes not applying
```bash
# Restart dev server after config changes
npm run dev

# Check tailwind.config.js content paths
```

### Issue: Port already in use
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

### Issue: Module not found errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `UI_SPEC_PRODUCTION.md` | Complete UI specification |
| `vc-filter-ui/src/App.tsx` | Main app entry with routing |
| `vc-filter-ui/src/components/layout/AppShell.tsx` | Layout shell |
| `vc-filter-ui/src/pages/RunSetupPage.tsx` | Run Setup page |
| `vc-filter-ui/src/pages/ResultsListPage.tsx` | Results page |
| `vc-filter-ui/src/pages/MemoViewPage.tsx` | Memo view page |
| `vc-filter-ui/tailwind.config.js` | Tailwind configuration |
| `vc-filter-ui/src/index.css` | Global styles |

---

## Next Steps After Launch

1. **Verify UI renders correctly** - Check all 3 pages
2. **Test navigation flow** - Run Setup → Results → Memo → Back
3. **Connect to backend** - Wire up API calls
4. **Add real data** - Replace mock data with API responses
5. **Implement remaining features** - File upload, filtering, export

---

**Questions?** Refer to `UI_SPEC_PRODUCTION.md` for detailed component specifications, design tokens, and acceptance criteria.
