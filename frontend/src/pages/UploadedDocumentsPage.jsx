import { useCallback, useEffect, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Files,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Trash2,
} from 'lucide-react'
import { API_URL } from '../services/api'

// How often (in milliseconds) to re-check the list while a file is processing.
const POLL_INTERVAL_MS = 3000

const FILTERS = ['All', 'Ready', 'Processing', 'Failed']

function formatSize(bytes) {
  // \u2014 is a long dash, shown when the size is unknown.
  if (typeof bytes !== 'number') return '\u2014'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

function formatDate(source) {
  const timestamp = source.uploaded_at || source.upload_at

  if (!timestamp) return 'Date unavailable'

  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return 'Date unavailable'

  const formatted = new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)

  // \u00b7 is a middle dot used as a separator.
  return source.timestamp_is_estimated
    ? `${formatted} \u00b7 Estimated`
    : formatted
}

// Maps the backend status to the filter group it belongs to.
function getGroup(status) {
  if (status === 'Processing') return 'Processing'
  if (status === 'Failed') return 'Failed'
  return 'Ready'
}

function StatusBadge({ status }) {
  const group = getGroup(status)

  if (group === 'Failed') {
    return (
      <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-red-500/20 bg-red-500/10 px-2.5 py-1 text-xs text-red-400">
        <AlertCircle size={12} />
        Failed
      </span>
    )
  }

  if (group === 'Processing') {
    return (
      <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-violet-400/20 bg-violet-400/10 px-2.5 py-1 text-xs text-violet-200">
        <Loader2 size={12} className="animate-spin" />
        Processing
      </span>
    )
  }

  return (
    <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400">
      <CheckCircle2 size={12} />
      {status || 'Processed'}
    </span>
  )
}

function UploadedDocumentsPage({ onNavigate }) {
  const [sources, setSources] = useState([])
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('All')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [confirmingFilename, setConfirmingFilename] = useState(null)
  const [deletingFilename, setDeletingFilename] = useState(null)
  const [actionError, setActionError] = useState('')

  // showSpinner = true: the user opened the page or pressed Refresh, so we
  // show the spinner and any error.
  // showSpinner = false: the automatic check every 3 seconds. It stays
  // silent so the list does not flicker.
  const fetchSources = useCallback(async (showSpinner = true) => {
    if (showSpinner) {
      setLoading(true)
      setError('')
    }

    try {
      const response = await fetch(`${API_URL}/sources`)
      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to load documents.')
      }

      setSources(Array.isArray(data.sources) ? data.sources : [])
    } catch (err) {
      if (showSpinner) {
        setError(err.message || 'Unable to connect to the backend.')
      }
    } finally {
      if (showSpinner) {
        setLoading(false)
      }
    }
  }, [])

  // Load the list once when the page opens.
  useEffect(() => {
    fetchSources()
  }, [fetchSources])

  const counts = {
    All: sources.length,
    Ready: sources.filter((s) => getGroup(s.status) === 'Ready').length,
    Processing: sources.filter((s) => getGroup(s.status) === 'Processing')
      .length,
    Failed: sources.filter((s) => getGroup(s.status) === 'Failed').length,
  }

  const hasProcessing = counts.Processing > 0

  // While a file is processing, re-check every 3 seconds. When none is,
  // this effect re-runs without a timer, so polling stops by itself.
  useEffect(() => {
    if (!hasProcessing) return undefined

    const timer = setInterval(() => {
      fetchSources(false)
    }, POLL_INTERVAL_MS)

    return () => clearInterval(timer)
  }, [hasProcessing, fetchSources])

  const deleteSource = async (filename) => {
    setDeletingFilename(filename)
    setActionError('')

    try {
      const response = await fetch(
        `${API_URL}/sources/${encodeURIComponent(filename)}`,
        { method: 'DELETE' }
      )
      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to delete the document.')
      }

      setSources((current) =>
        current.filter((source) => source.filename !== filename)
      )
      setConfirmingFilename(null)
    } catch (err) {
      setActionError(err.message || 'Unable to delete the document.')
    } finally {
      setDeletingFilename(null)
    }
  }

  const query = search.trim().toLowerCase()

  const visibleSources = sources.filter((source) => {
    const matchesSearch = source.filename?.toLowerCase().includes(query)
    const matchesFilter =
      filter === 'All' || getGroup(source.status) === filter

    return matchesSearch && matchesFilter
  })

  const totalSize = sources.reduce(
    (total, source) => total + (Number(source.size) || 0),
    0
  )

  const statCards = [
    { label: 'Documents', value: counts.All, icon: Files, tone: 'text-zinc-400' },
    { label: 'Ready', value: counts.Ready, icon: CheckCircle2, tone: 'text-emerald-400' },
    { label: 'Processing', value: counts.Processing, icon: Loader2, tone: 'text-violet-300' },
    { label: 'Failed', value: counts.Failed, icon: AlertCircle, tone: 'text-red-400' },
  ]

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 lg:px-8">
      {/* Header */}
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-lg font-medium tracking-tight text-zinc-100">
            Uploaded Documents
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            Every PDF your assistant can answer from.
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={() => fetchSources()}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-xs text-zinc-300 transition hover:bg-white/[0.05] disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>

          {onNavigate && (
            <button
              type="button"
              onClick={() => onNavigate('Knowledge Sources')}
              className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-3.5 py-2 text-xs font-medium text-white transition hover:bg-violet-500"
            >
              <Plus size={14} />
              <span className="hidden sm:inline">Add source</span>
              <span className="sm:hidden">Add</span>
            </button>
          )}
        </div>
      </header>

      {/* Stat cards */}
      <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {statCards.map(({ label, value, icon: Icon, tone }) => (
          <div
            key={label}
            className="min-w-0 rounded-xl border border-white/[0.08] bg-white/[0.02] p-4"
          >
            <div className={`flex items-center gap-2 text-xs ${tone}`}>
              <Icon size={14} />
              <span className="text-zinc-400">{label}</span>
            </div>
            <p className="mt-2 text-2xl font-medium text-zinc-100">{value}</p>
          </div>
        ))}
      </div>

      {/* Toolbar */}
      <div className="mt-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div
          role="tablist"
          aria-label="Filter documents"
          className="flex flex-wrap gap-1.5"
        >
          {FILTERS.map((name) => {
            const isActive = filter === name

            return (
              <button
                key={name}
                type="button"
                role="tab"
                aria-selected={isActive}
                onClick={() => setFilter(name)}
                className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs transition ${
                  isActive
                    ? 'bg-violet-500/10 font-medium text-violet-200'
                    : 'text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100'
                }`}
              >
                {name}
                <span
                  className={`rounded-full px-1.5 text-[11px] ${
                    isActive
                      ? 'bg-violet-400/20 text-violet-200'
                      : 'bg-white/[0.06] text-zinc-500'
                  }`}
                >
                  {counts[name]}
                </span>
              </button>
            )
          })}
        </div>

        <label className="flex w-full items-center gap-2 rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2 focus-within:border-violet-500/60 md:w-72 lg:w-96">
          <Search size={15} className="shrink-0 text-zinc-500" />
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search documents..."
            aria-label="Search documents"
            className="min-w-0 flex-1 bg-transparent text-sm text-zinc-200 outline-none placeholder:text-zinc-500"
          />
        </label>
      </div>

      {actionError && (
        <p role="alert" className="mt-3 text-sm text-red-400">
          {actionError}
        </p>
      )}

      {/* Document list */}
      <div className="mt-3">
        {error ? (
          <div className="rounded-xl border border-red-400/20 bg-red-400/[0.06] px-4 py-4 text-sm text-red-300">
            {error}
            <button
              type="button"
              onClick={() => fetchSources()}
              className="ml-3 text-violet-300 hover:text-violet-200"
            >
              Retry
            </button>
          </div>
        ) : loading && sources.length === 0 ? (
          <p className="py-8 text-sm text-zinc-400">Loading documents...</p>
        ) : sources.length === 0 ? (
          <div className="flex flex-col items-center rounded-xl border border-dashed border-white/10 bg-white/[0.015] px-5 py-14 text-center">
            <div className="mb-4 flex size-12 items-center justify-center rounded-xl bg-violet-500/10">
              <Files size={22} className="text-violet-400" />
            </div>
            <h2 className="text-sm font-medium text-zinc-200">
              No documents yet
            </h2>
            <p className="mt-1.5 text-sm text-zinc-500">
              Add a PDF and your assistant can start answering from it.
            </p>
            {onNavigate && (
              <button
                type="button"
                onClick={() => onNavigate('Knowledge Sources')}
                className="mt-5 inline-flex items-center gap-2 rounded-lg bg-violet-600 px-3.5 py-2 text-xs font-medium text-white transition hover:bg-violet-500"
              >
                <Plus size={14} />
                Add a PDF
              </button>
            )}
          </div>
        ) : visibleSources.length === 0 ? (
          <p className="py-8 text-sm text-zinc-500">
            No documents match your search or filter.
          </p>
        ) : (
          <div className="rounded-xl border border-white/[0.08] px-4">
            <p className="border-b border-white/[0.06] py-3 text-xs text-zinc-500">
              {visibleSources.length}{' '}
              {visibleSources.length === 1 ? 'file' : 'files'}
              {' \u00b7 '}
              {formatSize(totalSize)} total
            </p>

            <ul className="divide-y divide-white/[0.06]">
              {visibleSources.map((source) => {
                const isConfirming = confirmingFilename === source.filename
                const isDeleting = deletingFilename === source.filename
                // A file that is still processing cannot be deleted.
                const isProcessing = source.status === 'Processing'
                const isFailed = source.status === 'Failed'

                return (
                  <li
                    key={source.filename}
                    className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-2 py-3.5"
                  >
                    <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-white/[0.04] text-zinc-400">
                      <FileText size={17} />
                    </div>

                    <div className="min-w-0 flex-1 basis-40">
                      <p className="truncate text-sm font-medium text-zinc-200">
                        {source.filename}
                      </p>
                      <p className="mt-0.5 text-xs leading-5 text-zinc-500">
                        {formatSize(source.size)}
                        {' \u00b7 '}
                        {formatDate(source)}
                      </p>
                      {isFailed && (
                        <p className="mt-1 text-xs leading-5 text-red-400/90">
                          Processing failed. Delete it and upload the file
                          again.
                        </p>
                      )}
                    </div>

                    <StatusBadge status={source.status} />

                    <div className="flex shrink-0 items-center gap-2">
                      {isConfirming ? (
                        <>
                          <span className="text-xs text-zinc-400">
                            Delete this file?
                          </span>
                          <button
                            type="button"
                            onClick={() => setConfirmingFilename(null)}
                            disabled={isDeleting}
                            className="rounded-lg border border-white/10 px-2.5 py-1 text-xs text-zinc-300 transition hover:bg-white/[0.06] disabled:opacity-50"
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            onClick={() => deleteSource(source.filename)}
                            disabled={isDeleting}
                            className="rounded-lg border border-red-500/30 bg-red-500/10 px-2.5 py-1 text-xs text-red-400 transition hover:bg-red-500/20 disabled:opacity-50"
                          >
                            {isDeleting ? 'Deleting...' : 'Delete'}
                          </button>
                        </>
                      ) : (
                        <button
                          type="button"
                          aria-label={`Delete ${source.filename}`}
                          title={
                            isProcessing
                              ? 'Wait until processing finishes'
                              : 'Delete'
                          }
                          onClick={() => {
                            setActionError('')
                            setConfirmingFilename(source.filename)
                          }}
                          disabled={deletingFilename !== null || isProcessing}
                          className="rounded-lg p-2 text-zinc-500 transition hover:bg-red-500/10 hover:text-red-400 disabled:opacity-50"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </li>
                )
              })}
            </ul>
          </div>
        )}
      </div>
    </section>
  )
}

export default UploadedDocumentsPage