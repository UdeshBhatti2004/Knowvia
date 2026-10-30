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
  // A sample question picked on Overview, waiting for Test Assistant to use it.
  const [pendingQuestion, setPendingQuestion] = useState('')

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

  function handleAskSample(question) {
    setPendingQuestion(question)
    setActivePage('Test Assistant')
  }

  function renderPage() {
    switch (activePage) {
      case 'Overview':
        return (
          <OverviewPage
            onNavigate={handleNavigate}
            onAskSample={handleAskSample}
          />
        )

      case 'Knowledge Sources':
        return <KnowledgeSourcesPage onNavigate={handleNavigate} />

      case 'Uploaded Documents':
        return <UploadedDocumentsPage onNavigate={handleNavigate} />

      case 'Assistant Setup':
        return <AssistantSetupPage />

      case 'Settings':
        return <SettingsPage />

      case 'Test Assistant':
      default:
        return (
          <AskPage
            initialQuestion={pendingQuestion}
            onInitialQuestionUsed={() => setPendingQuestion('')}
          />
        )
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