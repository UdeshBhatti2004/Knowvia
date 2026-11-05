import { useEffect, useState } from 'react'
import AppLayout from './components/layout/AppLayout'
import AskPage from './pages/AskPage'
import KnowledgeSourcesPage from './pages/KnowledgeSourcesPage'
import UploadedDocumentsPage from './pages/UploadedDocumentsPage'
import AssistantSetupPage from './pages/AssistantSetupPage'
import InstallPage from './pages/InstallPage'
import ConversationsPage from './pages/ConversationsPage'
import OverviewPage from './pages/OverviewPage'
import SettingsPage from './pages/SettingsPage'

const AVAILABLE_PAGES = [
  'Overview',
  'Knowledge Sources',
  'Uploaded Documents',
  'Test Assistant',
  'Conversations',
  'Assistant Setup',
  'Install',
  'Settings',
]

// Page name <-> URL hash, e.g. 'Knowledge Sources' <-> '#knowledge-sources'
function pageToHash(page) {
  return '#' + page.toLowerCase().replace(/ /g, '-')
}

function pageFromHash() {
  const hash = window.location.hash
  const match = AVAILABLE_PAGES.find((page) => pageToHash(page) === hash)
  return match || 'Overview'
}

function App() {
  const [activePage, setActivePage] = useState(pageFromHash)
  // A sample question picked on Overview, waiting for Test Assistant to use it.
  const [pendingQuestion, setPendingQuestion] = useState('')

  // Browser back/forward or a manual hash change updates the page.
  useEffect(() => {
    const onHashChange = () => setActivePage(pageFromHash())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  function goTo(page) {
    setActivePage(page)
    const hash = pageToHash(page)
    if (window.location.hash !== hash) window.location.hash = hash
  }

  function handleNavigate(page) {
    if (AVAILABLE_PAGES.includes(page)) {
      goTo(page)
    }
  }

  function handleAskSample(question) {
    setPendingQuestion(question)
    goTo('Test Assistant')
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

      case 'Conversations':
        return <ConversationsPage onNavigate={handleNavigate} />

      case 'Install':
        return <InstallPage />

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