import { useEffect, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  Loader2,
  MessagesSquare,
  RefreshCw,
  SearchX,
} from 'lucide-react'
import { API_URL, apiFetch } from '../services/api'

const FILTERS = [
  { value: 'not_found', label: 'Not found' },
  { value: 'answered', label: 'Answered' },
  { value: 'off_topic', label: 'Off-topic' },
  { value: '', label: 'All' },
]

const OUTCOME_STYLES = {
  answered: {
    label: 'Answered',
    icon: CheckCircle2,
    className: 'text-emerald-400',
  },
  not_found: {
    label: 'Not found',
    icon: SearchX,
    className: 'text-amber-400',
  },
  off_topic: {
    label: 'Off-topic',
    icon: AlertCircle,
    className: 'text-zinc-400',
  },
}

function timeAgo(timestamp) {
  if (!timestamp) return 'Date unavailable'

  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return 'Date unavailable'

  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return 'Just now'

  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} min ago`

  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} hr ago`

  const days = Math.floor(hours / 24)
  if (days < 30) return `${days} ${days === 1 ? 'day' : 'days'} ago`

  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(date)
}

function itemKey(item) {
  return `${item.outcome}:${item.question}`
}

function OutcomeBadge({ outcome }) {
  const style = OUTCOME_STYLES[outcome] ?? OUTCOME_STYLES.answered
  const Icon = style.icon

  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 text-xs ${style.className}`}
    >
      <Icon size={13} />
      {style.label}
    </span>
  )
}

function emptyCopy(filter) {
  if (filter === 'not_found') {
    return {
      title: 'Nothing missing',
      body: 'No customer question has gone unanswered. Great sign.',
    }
  }
  if (filter) {
    return {
      title: 'Nothing here yet',
      body: 'No conversations match this filter.',
    }
  }
  return {
    title: 'No customer questions yet',
    body: 'Questions from your share link and website widget will show up here. Questions you ask in Test Assistant are not recorded.',
  }
}

function ConversationsPage({ onNavigate }) {
  const [filter, setFilter] = useState('not_found')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [openKey, setOpenKey] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      setError('')

      try {
        const query = new URLSearchParams({ limit: '100' })
        if (filter) query.set('outcome', filter)

        const response = await apiFetch(
          `${API_URL}/conversations/grouped?${query}`,
        )
        const data = await response.json().catch(() => ({}))

        if (!response.ok) {
          throw new Error(data.detail || 'Unable to load conversations.')
        }
        if (!cancelled) setItems(Array.isArray(data.items) ? data.items : [])
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof TypeError
              ? 'Could not reach the server.'
              : err.message,
          )
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [filter, reloadKey])

  const showEmpty = !loading && !error && items.length === 0
  const empty = emptyCopy(filter)

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 lg:px-8">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-lg font-medium tracking-tight text-zinc-100">
            Conversations
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            What customers ask through your share link and widget. Repeated
            questions are grouped.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setReloadKey((key) => key + 1)}
          disabled={loading}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-white/10 px-3 py-2 text-xs text-zinc-400 transition hover:bg-white/[0.04] hover:text-zinc-100 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </header>

      <div className="mt-5 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => {
              setFilter(f.value)
              setOpenKey(null)
            }}
            className={`rounded-full border px-3 py-1 text-xs transition ${
              filter === f.value
                ? 'border-violet-400/30 bg-violet-500/10 font-medium text-violet-200'
                : 'border-white/10 text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <div
          role="alert"
          className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm text-red-300"
        >
          <span>{error}</span>
          <button
            type="button"
            onClick={() => setReloadKey((key) => key + 1)}
            className="rounded-lg border border-red-400/30 px-3 py-1.5 text-xs font-medium text-red-200 transition hover:bg-red-400/10"
          >
            Try again
          </button>
        </div>
      )}

      {loading && items.length === 0 && !error && (
        <div className="mt-8 flex items-center gap-2 text-sm text-zinc-400">
          <Loader2 size={15} className="animate-spin" />
          Loading conversations...
        </div>
      )}

      {showEmpty && (
        <div className="mt-6 rounded-xl border border-white/[0.08] bg-white/[0.02] p-6 text-center">
          <div className="mx-auto flex size-10 items-center justify-center rounded-lg bg-white/[0.04] text-zinc-400">
            <MessagesSquare size={18} />
          </div>
          <p className="mt-3 text-sm font-medium text-zinc-200">
            {empty.title}
          </p>
          <p className="mt-1 text-xs leading-5 text-zinc-500">{empty.body}</p>
          {!filter && (
            <button
              type="button"
              onClick={() => onNavigate('Install')}
              className="mt-4 rounded-lg bg-violet-600 px-3.5 py-2 text-xs font-medium text-white transition hover:bg-violet-500"
            >
              Get share link
            </button>
          )}
        </div>
      )}

      {items.length > 0 && (
        <div className="mt-5 rounded-xl border border-white/[0.08] px-4">
          {items.map((item) => {
            const key = itemKey(item)
            const isOpen = openKey === key

            return (
              <div
                key={key}
                className="border-b border-white/[0.06] py-3 last:border-b-0"
              >
                <button
                  type="button"
                  onClick={() => setOpenKey(isOpen ? null : key)}
                  aria-expanded={isOpen}
                  className="flex w-full items-start gap-3 text-left"
                >
                  <div className="min-w-0 flex-1">
                    <p className="break-words text-sm text-zinc-200">
                      {item.question}
                    </p>
                    <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
                      <OutcomeBadge outcome={item.outcome} />
                      {item.count > 1 && (
                        <span className="rounded-full bg-white/[0.06] px-2 py-0.5 text-[11px] font-medium text-zinc-300">
                          ×{item.count}
                        </span>
                      )}
                      <span className="text-xs text-zinc-500">
                        {timeAgo(item.last_asked)}
                      </span>
                    </div>
                  </div>
                  <ChevronDown
                    size={15}
                    className={`mt-1 shrink-0 text-zinc-500 transition ${
                      isOpen ? 'rotate-180' : ''
                    }`}
                  />
                </button>

                {isOpen && (
                  <div className="mt-3 rounded-lg bg-white/[0.04] px-3.5 py-2.5">
                    <p className="whitespace-pre-wrap break-words text-sm leading-6 text-zinc-300">
                      {item.answer}
                    </p>
                    {item.sources.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {item.sources.map((source) => (
                          <span
                            key={source}
                            className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[11px] text-zinc-400"
                          >
                            {source}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

export default ConversationsPagey