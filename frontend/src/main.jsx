import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import LoginPage from './pages/LoginPage.jsx'
import PublicChatPage from './pages/PublicChatPage.jsx'
import { getToken } from './services/api'

const isPublicChat = window.location.pathname.startsWith('/chat')

function DashboardRoot() {
  const [authed, setAuthed] = useState(() => Boolean(getToken()))

  useEffect(() => {
    const onLogout = () => setAuthed(false)
    window.addEventListener('knowvia:logout', onLogout)
    return () => window.removeEventListener('knowvia:logout', onLogout)
  }, [])

  if (!authed) return <LoginPage onLoggedIn={() => setAuthed(true)} />
  return <App />
}

createRoot(document.getElementById('root')).render(
  <StrictMode>{isPublicChat ? <PublicChatPage /> : <DashboardRoot />}</StrictMode>,
)