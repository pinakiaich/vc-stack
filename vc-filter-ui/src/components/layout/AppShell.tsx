import { ReactNode, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Upload, List, FileText, Loader2, Search } from 'lucide-react'
import { useAppStore } from '../../store/appStore'
import { useHealthCheck } from '../../hooks'

interface AppShellProps {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const location = useLocation()
  const { state } = useAppStore()
  const { checking } = useHealthCheck()
  
  const navItems = [
    { id: 'run-setup', label: 'Run Setup', icon: Upload, href: '/' },
    { id: 'research', label: 'Research', icon: Search, href: '/research' },
    { id: 'results', label: 'Results', icon: List, href: '/results', badge: state.filterResults.length || undefined },
    { id: 'memo', label: 'Memo', icon: FileText, href: '/memo' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
              <span className="text-2xl">🎯</span>
              <span className="font-semibold text-gray-900">VC Firm Filter</span>
            </Link>
            
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
                        ? 'bg-blue-50 text-blue-700' 
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <item.icon className="w-4 h-4 mr-2" />
                    {item.label}
                    {item.badge && (
                      <span className="ml-2 px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                        {item.badge}
                      </span>
                    )}
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
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-20">
        {children}
      </main>

      {/* Status Bar */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 py-2 px-4">
        <div className="max-w-7xl mx-auto flex items-center space-x-4 text-xs text-gray-500">
          {/* API Status */}
          <span className="flex items-center">
            {checking ? (
              <>
                <Loader2 className="w-3 h-3 mr-1.5 animate-spin text-blue-500" />
                <span className="text-blue-600">Checking API...</span>
              </>
            ) : state.apiConnected ? (
              <>
                <span className="w-2 h-2 bg-green-500 rounded-full mr-1.5"></span>
                <span className="text-green-600">API Connected</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 bg-red-500 rounded-full mr-1.5"></span>
                <span className="text-red-600">API Disconnected</span>
              </>
            )}
          </span>
          
          {/* Cache Status */}
          {state.filterMetadata?.cacheHitRate !== undefined && (
            <span className="flex items-center">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-1.5"></span>
              Cache: {Math.round(state.filterMetadata.cacheHitRate * 100)}% hit rate
            </span>
          )}
          
          {/* File Status */}
          {state.uploadedFile && (
            <span className="flex items-center">
              <span className="w-2 h-2 bg-purple-500 rounded-full mr-1.5"></span>
              File: {state.uploadedFile.name}
            </span>
          )}
          
          {/* Results Count */}
          {state.filterResults.length > 0 && (
            <span className="flex items-center">
              <span className="w-2 h-2 bg-amber-500 rounded-full mr-1.5"></span>
              {state.filterResults.length} results
            </span>
          )}
        </div>
      </footer>
    </div>
  )
}
