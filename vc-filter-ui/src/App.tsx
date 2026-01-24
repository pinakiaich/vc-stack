import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppProvider } from './store/appStore'
import { AppShell } from './components/layout/AppShell'
import { RunSetupPage } from './pages/RunSetupPage'
import { ResearchPage } from './pages/ResearchPage'
import { ResultsListPage } from './pages/ResultsListPage'
import { MemoViewPage } from './pages/MemoViewPage'

function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<RunSetupPage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/results" element={<ResultsListPage />} />
            <Route path="/memo/:id" element={<MemoViewPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </AppProvider>
  )
}

export default App
