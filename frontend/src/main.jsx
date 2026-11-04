import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import App from './App.jsx'
import LoginPage from './pages/LoginPage.jsx'
import PublicChatPage from './pages/PublicChatPage.jsx'
import { getToken } from './services/api'

const isPublicChat = window.location.pathname.startsWith('/chat')

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
})

function DashboardRoot() {
  const [authed, setAuthed] = useState(() => Boolean(getToken()))

  useEffect(() => {
    const onLogout = () => {
      // Drop all cached data so the next account never sees old numbers.
      queryClient.clear()
      setAuthed(false)
    }
    window.addEventListener('knowvia:logout', onLogout)
    return () => window.removeEventListener('knowvia:logout', onLogout)
  }, [])

  if (!authed) return <LoginPage onLoggedIn={() => setAuthed(true)} />

  return (
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>{isPublicChat ? <PublicChatPage /> : <DashboardRoot />}</StrictMode>,
)