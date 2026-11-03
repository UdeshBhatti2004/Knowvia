import { useEffect, useRef, useState } from 'react'
import { Bot, Send, Loader2, AlertCircle, User } from 'lucide-react'
import { motion } from 'motion/react'
import { API_URL } from '../services/api'

const params = new URLSearchParams(window.location.search)
const WIDGET_KEY = params.get('key') || ''

function authHeaders() {
  return { 'X-Widget-Key': WIDGET_KEY }
}

function BotAvatar() {
  return (
    <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-violet-500/15 text-violet-200">
      <Bot size={14} />
    </div>
  )
}

function UserAvatar() {
  return (
    <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-white/[0.06] text-zinc-400">
      <User size={14} />
    </div>
  )
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
        // Two different 429s: the monthly plan limit, and the per-visitor
        // rate limit. Tell them apart by the message in the body.
        let detail = ''
        try {
          detail = (await response.json()).detail || ''
        } catch {
          // body was not JSON, treat as a normal rate limit
        }

        if (String(detail).includes('monthly question limit')) {
          throw new Error(
            'This assistant is unavailable right now. Please contact the business directly.',
          )
        }
        throw new Error(
          'Too many questions. Please wait a moment and try again.',
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
      <div className="flex h-dvh w-full items-center justify-center bg-[#0c0c0f] p-6">
        <div className="flex items-center gap-2 text-sm text-zinc-400">
          <AlertCircle className="size-4 text-red-400" />
          {setupError}
        </div>
      </div>
    )
  }

  if (!assistant) {
    return (
      <div className="flex h-dvh w-full items-center justify-center bg-[#0c0c0f]">
        <Loader2 className="size-5 animate-spin text-zinc-500" />
      </div>
    )
  }

  return (
    <div className="flex h-dvh w-full flex-col bg-[#0c0c0f] text-white">
      <header className="flex shrink-0 items-center gap-3 border-b border-white/[0.08] bg-[#111114] px-4 py-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-violet-600">
          <Bot size={18} />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-zinc-100">
            {assistant.name}
          </p>
          <p className="text-[11px] text-zinc-500">Business assistant</p>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto p-4">
        <div className="flex w-11/12 items-start gap-2.5 self-start sm:w-3/4">
          <BotAvatar />
          <p className="min-w-0 break-words rounded-2xl rounded-tl-sm bg-white/[0.05] px-3.5 py-2.5 text-sm leading-6 text-zinc-200">
            {assistant.welcome_message}
          </p>
        </div>

        {messages.map((m, i) => {
          if (m.role === 'user') {
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.15 }}
                className="flex w-11/12 items-start justify-end gap-2.5 self-end sm:w-3/4"
              >
                <p className="min-w-0 whitespace-pre-wrap break-words rounded-2xl rounded-tr-sm bg-violet-600 px-3.5 py-2.5 text-sm leading-6 text-white">
                  {m.text}
                </p>
                <UserAvatar />
              </motion.div>
            )
          }

          if (m.role === 'error') {
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.15 }}
                className="flex w-11/12 items-start gap-2.5 self-start sm:w-3/4"
              >
                <BotAvatar />
                <p className="min-w-0 break-words rounded-2xl rounded-tl-sm border border-red-400/20 bg-red-400/10 px-3.5 py-2.5 text-sm leading-6 text-red-300">
                  {m.text}
                </p>
              </motion.div>
            )
          }

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.15 }}
              className="flex w-11/12 items-start gap-2.5 self-start sm:w-3/4"
            >
              <BotAvatar />
              <div className="min-w-0">
                <p className="whitespace-pre-wrap break-words rounded-2xl rounded-tl-sm bg-white/[0.05] px-3.5 py-2.5 text-sm leading-6 text-zinc-200">
                  {m.text}
                </p>
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1.5 px-1">
                    {m.sources.map((s, j) => (
                      <span
                        key={j}
                        className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[11px] text-zinc-400"
                      >
                        {s.source}
                        {s.page ? ` · p.${s.page}` : ''}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )
        })}

        {sending && (
          <div className="flex items-start gap-2.5 self-start">
            <BotAvatar />
            <div className="rounded-2xl rounded-tl-sm bg-white/[0.05] px-3.5 py-2.5">
              <Loader2 className="size-4 animate-spin text-zinc-400" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={handleSend}
        className="flex shrink-0 items-center gap-2 border-t border-white/[0.08] bg-[#111114] p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          maxLength={500}
          placeholder="Ask a question..."
          className="w-full flex-1 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5 text-sm text-white outline-none transition placeholder:text-zinc-600 focus:border-violet-400/50"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          aria-label="Send"
          className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-violet-600 text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-violet-600"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  )
}