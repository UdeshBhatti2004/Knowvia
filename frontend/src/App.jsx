
import { useState } from 'react'
import AppLayout from './components/layout/AppLayout'
import AskPage from './pages/AskPage'
import KnowledgeSourcesPage from './pages/KnowledgeSourcesPage'
import UploadedDocumentsPage from './pages/UploadedDocumentsPage'
import AssistantSetupPage from './pages/AssistantSetupPage'
import OverviewPage from './pages/OverviewPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  const [activePage, setActivePage] = useState('Overview')

  function handleNavigate(page) {
    const availablePages = [
      'Overview',
      'Knowledge Sources',
      'Uploaded Documents',
      'Test Assistant',
      'Assistant Setup',
      'Settings',
    ]

    if (availablePages.includes(page)) {
      setActivePage(page)
    }
  }

  function renderPage() {
    switch (activePage) {
      case 'Overview':
        return <OverviewPage onNavigate={handleNavigate} />

      case 'Knowledge Sources':
        return <KnowledgeSourcesPage onNavigate={handleNavigate} />

      case 'Uploaded Documents':
        return <UploadedDocumentsPage />

      case 'Assistant Setup':
        return <AssistantSetupPage />

      case 'Settings':
        return <SettingsPage />

      case 'Test Assistant':
      default:
        return <AskPage />
    }
  }

  return (
    <AppLayout
      activePage={activePage}
      onNavigate={handleNavigate}
    >
      {renderPage()}
    </AppLayout>
  )
}

export default App
