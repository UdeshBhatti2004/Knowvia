
import { useCallback, useEffect, useState } from 'react'
import { FileText, RefreshCw, Search } from 'lucide-react'
import { API_URL } from '../services/api'

function formatSize(bytes) {
  if (typeof bytes !== 'number') return '—'
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

  return source.timestamp_is_estimated
    ? `${formatted} · Estimated`
    : formatted
}

function UploadedDocumentsPage() {
  const [sources, setSources] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchSources = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const response = await fetch(`${API_URL}/sources`)
      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to load documents.')
      }

      setSources(Array.isArray(data.sources) ? data.sources : [])
    } catch (err) {
      setError(err.message || 'Unable to connect to the backend.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSources()
  }, [fetchSources])

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

      <button
        type="button"
        onClick={fetchSources}
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

    {/* Document list */}
    <div className="mt-2 w-full">
      {error ? (
        <div className="py-6 text-sm text-red-400">
          {error}
          <button
            type="button"
            onClick={fetchSources}
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
          {filteredSources.map((source) => (
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
                  {' · '}
                  {formatDate(source)}
                </p>
              </div>

              <span className="shrink-0 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400">
                {source.status || 'Processed'}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  </section>
)
}

export default UploadedDocumentsPage
