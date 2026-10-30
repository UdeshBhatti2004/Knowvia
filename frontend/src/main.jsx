import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import PublicChatPage from './pages/PublicChatPage.jsx'

const isPublicChat = window.location.pathname.startsWith('/chat')

createRoot(document.getElementById('root')).render(
  <StrictMode>{isPublicChat ? <PublicChatPage /> : <App />}</StrictMode>,
)
