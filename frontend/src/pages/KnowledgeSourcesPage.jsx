import { useRef, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Info,
  Plus,
  Upload,
  X,
} from 'lucide-react'
import { API_URL } from '../services/api'

const uploadIdeas = [
  'Course details and fees',
  'Class schedules and timings',
  'Refund and cancellation policy',
  'FAQs and contact information',
]

function KnowledgeSourcesPage({ onNavigate }) {
  const fileInputRef = useRef(null)

  const [selectedFile, setSelectedFile] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [notice, setNotice] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  function clearMessages() {
    setError('')
    setSuccess('')
    setNotice('')
  }

  function processFile(file) {
    if (!file) return

    clearMessages()

    if (
      file.type !== 'application/pdf' &&
      !file.name.toLowerCase().endsWith('.pdf')
    ) {
      setError('Please select a PDF file.')
      setSelectedFile(null)
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('PDF files must be 10 MB or smaller.')
      setSelectedFile(null)
      return
    }

    setSelectedFile(file)
  }

  async function handleUpload() {
    if (!selectedFile || isUploading) return

    setIsUploading(true)
    clearMessages()

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await fetch(`${API_URL}/sources/upload`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        const message = data.detail || 'Upload failed. Please try again.'

        // 409 means the document is already in the knowledge base
        // (same content, or same file name). That is not a failure.
        if (response.status === 409) {
          setNotice(message)
          setSelectedFile(null)
          return
        }

        throw new Error(message)
      }

      // The server replies as soon as the file is saved and embeds it in
      // the background, so we say "received", not "uploaded successfully".
      setSuccess(
        `${data.filename || selectedFile.name} received. ` +
          'It is being processed in the background.'
      )
      setSelectedFile(null)
    } catch (err) {
      setError(
        err.message || 'Unable to connect to the backend. Please try again.'
      )
    } finally {
      setIsUploading(false)
    }
  }

  function handleFileChange(event) {
    processFile(event.target.files?.[0])
    event.target.value = ''
  }

  function handleRemoveFile() {
    if (isUploading) return

    setSelectedFile(null)
    clearMessages()
  }

  function openFilePicker() {
    if (isUploading) return

    clearMessages()
    fileInputRef.current?.click()
  }

  function handleDrop(event) {
    event.preventDefault()
    setIsDragging(false)

    if (!isUploading) {
      processFile(event.dataTransfer.files?.[0])
    }
  }

  function handleZoneKeyDown(event) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      openFilePicker()
    }
  }

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 lg:px-8">
      {/* Header */}
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-lg font-medium tracking-tight text-zinc-100">
            Knowledge Sources
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            The documents your assistant answers from.
          </p>
        </div>

        <button
          type="button"
          onClick={openFilePicker}
          disabled={isUploading}
          className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-violet-600 px-3.5 py-2 text-xs font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Plus size={14} />
          <span className="hidden sm:inline">Add source</span>
          <span className="sm:hidden">Add</span>
        </button>
      </header>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Messages */}
      {error && (
        <div
          role="alert"
          className="mt-5 flex items-start gap-2.5 rounded-xl border border-red-400/20 bg-red-400/[0.06] px-4 py-3 text-sm text-red-300"
        >
          <AlertCircle size={16} className="mt-0.5 shrink-0" />
          <p className="min-w-0 break-words">{error}</p>
        </div>
      )}

      {notice && (
        <div
          role="status"
          className="mt-5 flex items-start gap-2.5 rounded-xl border border-amber-400/20 bg-amber-400/[0.06] px-4 py-3 text-sm text-amber-300"
        >
          <Info size={16} className="mt-0.5 shrink-0" />
          <p className="min-w-0 break-words">{notice}</p>
        </div>
      )}

      {success && (
        <div
          role="status"
          className="mt-5 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border border-emerald-400/20 bg-emerald-400/[0.06] px-4 py-3 text-sm text-emerald-300"
        >
          <CheckCircle2 size={16} className="shrink-0" />
          <p className="min-w-0 flex-1 basis-48 break-words">{success}</p>
          {onNavigate && (
            <button
              type="button"
              onClick={() => onNavigate('Uploaded Documents')}
              className="shrink-0 text-xs font-medium text-emerald-200 underline-offset-2 transition hover:underline"
            >
              View progress
            </button>
          )}
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Upload area */}
        <div className="min-w-0 lg:col-span-2">
          {selectedFile ? (
            <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
              <p className="text-xs text-zinc-500">Ready to upload</p>

              <div className="mt-3 flex flex-wrap items-center gap-3">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-violet-500/10">
                  <FileText size={20} className="text-violet-400" />
                </div>

                <div className="min-w-0 flex-1 basis-40">
                  <p className="truncate text-sm font-medium text-zinc-200">
                    {selectedFile.name}
                  </p>
                  <p className="mt-1 text-xs text-zinc-500">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    {' \u00b7 '}
                    {isUploading ? 'Uploading...' : 'PDF'}
                  </p>
                </div>

                <div className="flex shrink-0 items-center gap-2">
                  <button
                    type="button"
                    onClick={handleRemoveFile}
                    disabled={isUploading}
                    aria-label="Remove selected file"
                    className="rounded-lg p-2 text-zinc-400 transition hover:bg-white/[0.06] hover:text-white disabled:opacity-50"
                  >
                    <X size={16} />
                  </button>

                  <button
                    type="button"
                    onClick={handleUpload}
                    disabled={isUploading}
                    className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-3.5 py-2 text-xs font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isUploading && (
                      <span className="size-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    )}
                    {isUploading ? 'Uploading...' : 'Upload PDF'}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div
              role="button"
              tabIndex={0}
              aria-label="Select a PDF to upload"
              onClick={openFilePicker}
              onKeyDown={handleZoneKeyDown}
              onDragOver={(event) => {
                event.preventDefault()
                setIsDragging(true)
              }}
              onDragLeave={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget)) {
                  setIsDragging(false)
                }
              }}
              onDrop={handleDrop}
              className={`flex cursor-pointer flex-col items-center rounded-xl border border-dashed px-5 py-12 text-center outline-none transition-colors focus-visible:border-violet-400 sm:py-16 ${
                isDragging
                  ? 'border-violet-400 bg-violet-500/10'
                  : 'border-white/10 bg-white/[0.015] hover:border-white/20 hover:bg-white/[0.03]'
              }`}
            >
              <div className="mb-4 flex size-12 items-center justify-center rounded-xl bg-violet-500/10">
                <Upload size={22} className="text-violet-400" />
              </div>

              <h2 className="text-sm font-medium text-zinc-200">
                {isDragging ? 'Drop your PDF here' : 'Drag a PDF here'}
              </h2>

              <p className="mt-1.5 text-sm text-zinc-500">
                or click to choose a file from your computer
              </p>

              <p className="mt-4 text-xs text-zinc-600">
                PDF only {'\u00b7'} up to 10 MB {'\u00b7'} one file at a time
              </p>
            </div>
          )}
        </div>

        {/* Guidance */}
        <aside className="min-w-0 rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
          <h2 className="text-sm font-medium text-zinc-200">
            What to upload
          </h2>
          <p className="mt-1 text-xs leading-5 text-zinc-500">
            Anything your customers ask about often.
          </p>

          <ul className="mt-3 space-y-2">
            {uploadIdeas.map((idea) => (
              <li
                key={idea}
                className="flex items-start gap-2 text-sm text-zinc-300"
              >
                <CheckCircle2
                  size={15}
                  className="mt-0.5 shrink-0 text-violet-300"
                />
                {idea}
              </li>
            ))}
          </ul>

          <p className="mt-4 border-t border-white/[0.07] pt-3 text-xs leading-5 text-zinc-500">
            Uploading the same file twice is skipped automatically.
          </p>
        </aside>
      </div>
    </section>
  )
}

export default KnowledgeSourcesPage