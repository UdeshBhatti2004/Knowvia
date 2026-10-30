import { useEffect, useRef, useState } from 'react'
import { Bot, RotateCcw, User } from 'lucide-react'
import QuestionInput from '../components/chat/QuestionInput'
import AnswerCard from '../components/answers/AnswerCard'
import { API_URL } from '../services/api'

// Used until the saved settings load, and if loading them fails.
const DEFAULT_NAME = 'Knowvia Assistant'
const DEFAULT_WELCOME = 'How can I help you today?'

const suggestions = [
  'What courses do we offer?',
  'What is our refund policy?',
  'How long is the Python course?',
]

let nextMessageId = 1

function AssistantAvatar() {
  return (
    <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-violet-500/15 text-violet-200">
      <Bot size={16} />
    </div>
  )
}
function AskPage({ initialQuestion = '', onInitialQuestionUsed }) {

  const [question, setQuestion] = useState(initialQuestion)
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [assistant, setAssistant] = useState({
    name: DEFAULT_NAME,
    welcome: DEFAULT_WELCOME,
  })
  const bottomRef = useRef(null)

  // Load the saved assistant name and welcome message once.
  useEffect(() => {
    let cancelled = false

    async function loadAssistant() {
      try {
        const response = await fetch(`${API_URL}/assistant`)
        if (!response.ok) return
        const data = await response.json()
        if (cancelled) return
        setAssistant({
          name: data.name || DEFAULT_NAME,
          welcome: data.welcome_message || DEFAULT_WELCOME,
        })
      } catch {
        // Keep the defaults. The chat must work even if settings fail.
      }
    }

    loadAssistant()
    return () => {
      cancelled = true
    }
  }, [])

  // Keep the newest message in view.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isLoading])

    // A sample question from Overview pre-fills the input once, then is cleared
  // so it does not come back on the next visit.
  useEffect(() => {
    if (initialQuestion) onInitialQuestionUsed?.()
  }, [initialQuestion, onInitialQuestionUsed])

  async function handleSubmit(value = question) {
    const submittedQuestion = value.trim()

    if (!submittedQuestion || isLoading) return

    setQuestion('')
    setIsLoading(true)
    setMessages((current) => [
      ...current,
      { id: nextMessageId++, role: 'user', text: submittedQuestion },
    ])

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: submittedQuestion,
        }),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(
          data.detail || 'Unable to get an answer. Please try again.'
        )
      }

      setMessages((current) => [
        ...current,
        { id: nextMessageId++, role: 'assistant', result: data },
      ])
    } catch (err) {
      setMessages((current) => [
        ...current,
        {
          id: nextMessageId++,
          role: 'assistant',
          error:
            err.message ||
            'Unable to connect to Knowvia. Check that the backend is running.',
          retryQuestion: submittedQuestion,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  function handleNewChat() {
    if (isLoading) return

    setMessages([])
    setQuestion('')
  }

  const isEmpty = messages.length === 0

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
      {/* Header */}
      <header className="flex shrink-0 items-center justify-between gap-3 border-b border-white/[0.07] px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-2.5">
          <h1 className="text-lg font-medium tracking-tight text-zinc-100">
            Test Assistant
          </h1>
          <span className="rounded-full border border-violet-400/20 bg-violet-400/10 px-2.5 py-0.5 text-[11px] font-medium text-violet-200">
            Test mode
          </span>
        </div>

        <button
          type="button"
          onClick={handleNewChat}
          disabled={isEmpty || isLoading}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-zinc-300 transition hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <RotateCcw size={13} />
          New chat
        </button>
      </header>

      {/* Conversation */}
      <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto px-4 py-5 sm:px-6 lg:px-8">
        {/* Welcome message always opens the chat */}
        <div className="flex items-start gap-2.5">
          <AssistantAvatar />
          <div className="w-11/12 min-w-0 sm:w-4/5">
            <p className="mb-1 text-[11px] text-zinc-500">{assistant.name}</p>
            <p className="inline-block break-words rounded-2xl rounded-tl-sm bg-white/[0.05] px-4 py-2.5 text-sm leading-6 text-zinc-200">
              {assistant.welcome}
            </p>
          </div>
        </div>

        {isEmpty && !isLoading && (
          <div className="pl-[42px]">
            <p className="mb-2 text-xs text-zinc-500">Try asking</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => handleSubmit(item)}
                  className="rounded-full border border-white/10 px-3 py-2 text-left text-xs leading-5 text-zinc-400 transition hover:border-violet-400/30 hover:bg-violet-500/[0.06] hover:text-zinc-100 sm:text-sm"
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message) => {
          if (message.role === 'user') {
            return (
              <div key={message.id} className="flex items-start justify-end gap-2.5">
                <div className="flex w-11/12 min-w-0 justify-end sm:w-4/5">
                  <p className="break-words rounded-2xl rounded-tr-sm bg-violet-600 px-4 py-2.5 text-sm leading-6 text-white">
                    {message.text}
                  </p>
                </div>
                <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-white/[0.06] text-zinc-400">
                  <User size={16} />
                </div>
              </div>
            )
          }

          return (
            <div key={message.id} className="flex items-start gap-2.5">
              <AssistantAvatar />
              <div className="w-11/12 min-w-0 sm:w-4/5">
                <p className="mb-1 text-[11px] text-zinc-500">
                  {assistant.name}
                </p>

                {message.error ? (
                  <div className="rounded-2xl rounded-tl-sm border border-amber-400/15 bg-amber-400/5 px-4 py-3">
                    <p role="alert" className="text-sm leading-6 text-amber-200">
                      {message.error}
                    </p>
                    <button
                      type="button"
                      onClick={() => handleSubmit(message.retryQuestion)}
                      disabled={isLoading}
                      className="mt-2 text-xs text-violet-300 transition hover:text-violet-200 disabled:opacity-50"
                    >
                      Try again
                    </button>
                  </div>
                ) : (
                  <AnswerCard result={message.result} />
                )}
              </div>
            </div>
          )
        })}

        {/* Typing indicator */}
        {isLoading && (
          <div className="flex items-start gap-2.5" role="status">
            <AssistantAvatar />
            <div className="min-w-0">
              <p className="mb-1 text-[11px] text-zinc-500">{assistant.name}</p>
              <div className="inline-flex items-center gap-1.5 rounded-2xl rounded-tl-sm bg-white/[0.05] px-4 py-3">
                <span className="size-1.5 animate-bounce rounded-full bg-zinc-400 [animation-delay:-0.3s]" />
                <span className="size-1.5 animate-bounce rounded-full bg-zinc-400 [animation-delay:-0.15s]" />
                <span className="size-1.5 animate-bounce rounded-full bg-zinc-400" />
                <span className="sr-only">Searching your knowledge base...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input docked at the bottom */}
      <div className="shrink-0 border-t border-white/[0.07] px-4 py-3 sm:px-6 lg:px-8">
        <QuestionInput
          value={question}
          onChange={setQuestion}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </div>
    </section>
  )
}

export default AskPage