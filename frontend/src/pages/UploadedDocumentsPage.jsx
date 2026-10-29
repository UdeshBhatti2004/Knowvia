import { useCallback, useEffect, useState } from 'react'
import { FileText, RefreshCw, Search, Trash2 } from 'lucide-react'
import { API_URL } from '../services/api'

// How often (in milliseconds) to re-check the list while a file is processing.
const POLL_INTERVAL_MS = 3000

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

// NEW: one small component for the status badge, so the colours for each
// status live in one place.
function StatusBadge({ status }) {
  const value = status || 'Processed'

  // Failed: red.
  if (value === 'Failed') {
    return (
      <span className="shrink-0 rounded-full border border-red-500/20 bg-red-500/10 px-2.5 py-1 text-xs text-red-400">
        Failed
      </span>
    )
  }

  // Processing: amber, with a small spinning circle.
  if (value === 'Processing') {
    return (
      <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-amber-500/20 bg-amber-500/10 px-2.5 py-1 text-xs text-amber-400">
        <span className="size-3 animate-spin rounded-full border-2 border-amber-400/30 border-t-amber-400" />
        Processing
      </span>
    )
  }

  // Processed (or anything else): green, as before.
  return (
    <span className="shrink-0 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400">
      {value}
    </span>
  )
}

function UploadedDocumentsPage() {
  const [sources, setSources] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [confirmingFilename, setConfirmingFilename] = useState(null)
  const [deletingFilename, setDeletingFilename] = useState(null)
  const [actionError, setActionError] = useState('')

  // NEW: the argument `showSpinner` tells us who is asking.
  //  - true  (default): the user pressed Refresh or opened the page, so we
  //    show the spinner and any error.
  //  - false: the automatic check every 3 seconds. It stays silent, so the
  //    list does not flicker and a short network hiccup shows no error.
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
      // Only show errors for requests the user started.
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

  // NEW: true while at least one file is still being embedded.
  const hasProcessing = sources.some(
    (source) => source.status === 'Processing'
  )

  // NEW: polling. While a file is processing, re-check the list every
  // 3 seconds. When the list has no "Processing" file any more,
  // `hasProcessing` becomes false, this effect re-runs, and no timer is
  // started, so polling stops by itself.
  useEffect(() => {
    if (!hasProcessing) return undefined

    const timer = setInterval(() => {
      fetchSources(false)
    }, POLL_INTERVAL_MS)

    // Cleanup: stop the timer when the status changes or the page closes.
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

  const filteredSources = sources.filter((source) =>
    source.filename?.toLowerCase().includes(search.trim().toLowerCase())
  )

  const totalSize = sources.reduce(
    (total, source) => total + (Number(source.size) || 0),
    0
  )

  return (
    <section className="flex min-h-0 w-full min-w-0 flex-1 flex-col overflow-y-auto bg-[#0b0b0e] px-3 py-4 text-zinc-100 sm:px-6 sm:py-6 lg:px-10 lg:py-8">
      {/* Header */}
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-semibold tracking-tight sm:text-2xl">
            Uploaded Documents
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            All your uploaded PDFs in one place.
          </p>
        </div>

        {/* CHANGED: () => fetchSources() instead of onClick={fetchSources},
            because fetchSources now takes an argument and a bare reference
            would receive the click event as that argument. */}
        <button
          type="button"
          onClick={() => fetchSources()}
          disabled={loading}
          className="inline-flex shrink-0 items-center gap-2 rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2 text-sm text-zinc-300 transition hover:bg-white/[0.06] disabled:opacity-50"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </header>

      {/* Summary cards */}
      <div className="mt-5 grid w-full grid-cols-2 gap-3 sm:mt-6 sm:w-3/4 md:w-1/2 xl:w-2/5">
        <div className="min-w-0 rounded-xl border border-white/[0.08] bg-[#111114] px-3 py-3 sm:px-4">
          <p className="text-xs text-zinc-500">Documents</p>
          <p className="mt-1 truncate text-base font-semibold text-zinc-100 sm:text-lg">
            {sources.length}
          </p>
        </div>

        <div className="min-w-0 rounded-xl border border-white/[0.08] bg-[#111114] px-3 py-3 sm:px-4">
          <p className="text-xs text-zinc-500">Total size</p>
          <p className="mt-1 truncate text-base font-semibold text-zinc-100 sm:text-lg">
            {formatSize(totalSize)}
          </p>
        </div>
      </div>

      {/* Toolbar */}
      <div className="mt-6 flex flex-col gap-3 border-b border-white/[0.08] pb-4 sm:mt-8 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0">
          <h2 className="text-base font-medium">All documents</h2>
          <p className="mt-0.5 text-xs text-zinc-500">
            {sources.length} {sources.length === 1 ? 'file' : 'files'} in your
            knowledge base
          </p>
        </div>

        <label className="flex w-full items-center gap-2 rounded-lg border border-white/10 bg-[#111114] px-3 py-2 focus-within:border-violet-500/60 md:w-72 lg:w-96">
          <Search size={16} className="shrink-0 text-zinc-500" />
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
      <div className="mt-2 w-full">
        {error ? (
          <div className="py-6 text-sm text-red-400">
            {error}
            <button
              type="button"
              onClick={() => fetchSources()}
              className="ml-3 text-violet-400 hover:text-violet-300"
            >
              Retry
            </button>
          </div>
        ) : loading && sources.length === 0 ? (
          <p className="py-8 text-sm text-zinc-400">Loading documents...</p>
        ) : filteredSources.length === 0 ? (
          <p className="py-8 text-sm text-zinc-500">
            {search ? 'No matching documents.' : 'No documents uploaded yet.'}
          </p>
        ) : (
          <ul className="w-full divide-y divide-white/[0.06]">
            {filteredSources.map((source) => {
              const isConfirming = confirmingFilename === source.filename
              const isDeleting = deletingFilename === source.filename
              // NEW: a file that is still processing cannot be deleted.
              const isProcessing = source.status === 'Processing'

              return (
                <li
                  key={source.filename}
                  className="flex w-full min-w-0 flex-wrap items-center gap-x-3 gap-y-2 rounded-lg px-1 py-3 transition hover:bg-white/[0.02] sm:gap-x-4 sm:px-2 sm:py-4"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-violet-500/10">
                    <FileText size={19} className="text-violet-400" />
                  </div>

                  <div className="min-w-0 flex-1 basis-40">
                    <p className="truncate text-sm font-medium text-zinc-200">
                      {source.filename}
                    </p>
                    <p className="mt-1 text-xs leading-5 text-zinc-500">
                      {formatSize(source.size)}
                      {' \u00b7 '}
                      {formatDate(source)}
                    </p>
                  </div>

                  {/* CHANGED: the badge now depends on the status. */}
                  <StatusBadge status={source.status} />

                  <div className="flex shrink-0 items-center gap-2">
                    {isConfirming ? (
                      <>
                        <span className="text-xs text-zinc-400">
                          Delete this file?
                        </span>
                        {/* FIXED: "text-zinc-300transition" was missing a
                            space, so neither class worked. */}
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
                        // CHANGED: also disabled while this file is processing.
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
        )}
      </div>
    </section>
  )
}

export default UploadedDocumentsPage