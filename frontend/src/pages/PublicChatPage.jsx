import { useEffect, useRef, useState } from 'react'
import { Send, Loader2, AlertCircle } from 'lucide-react'
import { motion } from 'motion/react'
import { API_URL } from '../services/api'

const params = new URLSearchParams(window.location.search)
const WIDGET_KEY = params.get('key') || ''

function authHeaders() {
  return { 'X-Widget-Key': WIDGET_KEY }
}

export default function PublicChatPage() {
  const [assistant, setAssistant] = useState(null)
  const [setupError, setSetupError] = useState('')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    async function load() {
      if (!WIDGET_KEY) {
        setSetupError('Missing widget key.')
        return
      }
      try {
        const response = await fetch(`${API_URL}/public/assistant`, {
          headers: authHeaders(),
        })
        if (response.status === 401) {
          setSetupError('Invalid widget key.')
          return
        }
        if (!response.ok) throw new Error()
        setAssistant(await response.json())
      } catch {
        setSetupError('Could not load the assistant.')
      }
    }
    load()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  async function handleSend(event) {
    event.preventDefault()
    const question = input.trim()
    if (!question || sending || !assistant) return

    setMessages((prev) => [...prev, { role: 'user', text: question }])
    setInput('')
    setSending(true)

    try {
      const response = await fetch(`${API_URL}/public/ask`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (response.status === 429) {
        const wait = response.headers.get('Retry-After')
        throw new Error(
          wait
            ? `Too many questions. Try again in ${wait}s.`
            : 'Too many questions. Try again later.',
        )
      }
      if (response.status === 422) {
        throw new Error('Please enter a question up to 500 characters.')
      }
      if (!response.ok) throw new Error('Something went wrong. Try again.')

      const data = await response.json()
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: data.answer, sources: data.sources || [] },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'error',
          text: err.message || 'Something went wrong. Try again.',
        },
      ])
    } finally {
      setSending(false)
    }
  }

  if (setupError) {
    return (
      <div className="flex h-dvh w-full items-center justify-center bg-white p-6">
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <AlertCircle className="h-4 w-4 text-red-500" />
          {setupError}
        </div>
      </div>
    )
  }

  if (!assistant) {
    return (
      <div className="flex h-dvh w-full items-center justify-center bg-white">
        <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
      </div>
    )
  }

  return (
    <div className="flex h-dvh w-full flex-col bg-white">
      <header className="flex items-center gap-3 border-b border-slate-200 bg-slate-900 px-4 py-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-sm font-semibold text-white">
          {assistant.name.charAt(0).toUpperCase()}
        </div>
        <div className="text-sm font-semibold text-white">{assistant.name}</div>
      </header>

      <div className="flex flex-1 flex-col gap-3 overflow-y-auto bg-slate-50 p-4">
        <div className="w-3/4 self-start rounded-2xl rounded-tl-sm bg-white px-4 py-2.5 text-sm text-slate-800 shadow-sm">
          {assistant.welcome_message}
        </div>

        {messages.map((m, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.15 }}
            className={
              m.role === 'user'
                ? 'w-3/4 self-end rounded-2xl rounded-tr-sm bg-slate-900 px-4 py-2.5 text-sm text-white'
                : m.role === 'error'
                  ? 'w-3/4 self-start rounded-2xl rounded-tl-sm bg-red-50 px-4 py-2.5 text-sm text-red-700'
                  : 'w-3/4 self-start rounded-2xl rounded-tl-sm bg-white px-4 py-2.5 text-sm text-slate-800 shadow-sm'
            }
          >
            <div className="whitespace-pre-wrap">{m.text}</div>
            {m.sources && m.sources.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5 border-t border-slate-100 pt-2">
                {m.sources.map((s, j) => (
                  <span
                    key={j}
                    className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
                  >
                    {s.source} · p.{s.page}
                  </span>
                ))}
              </div>
            )}
          </motion.div>
        ))}

        {sending && (
          <div className="self-start rounded-2xl rounded-tl-sm bg-white px-4 py-2.5 shadow-sm">
            <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={handleSend}
        className="flex items-center gap-2 border-t border-slate-200 bg-white p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          maxLength={500}
          placeholder="Ask a question..."
          className="flex-1 rounded-full border border-slate-300 px-4 py-2 text-sm outline-none focus:border-slate-900"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-white disabled:opacity-40"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  )
}
