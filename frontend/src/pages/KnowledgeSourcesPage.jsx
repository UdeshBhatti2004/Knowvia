
import { useRef, useState } from 'react'
import { FileText, Plus, Upload, X } from 'lucide-react'

const API_URL = 'http://127.0.0.1:8000'

function KnowledgeSourcesPage() {
  const fileInputRef = useRef(null)

  const [selectedFile, setSelectedFile] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  function processFile(file) {
    if (!file) return

    setError('')
    setSuccess('')

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
    setError('')
    setSuccess('')

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      const response = await fetch(`${API_URL}/sources/upload`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed. Please try again.')
      }

      setSuccess(`${data.filename || selectedFile.name} uploaded successfully.`)
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
    setError('')
    setSuccess('')
  }

  function handleAddSource() {
    if (isUploading) return

    setError('')
    fileInputRef.current?.click()
  }

  function handleDrop(event) {
    event.preventDefault()
    setIsDragging(false)

    if (!isUploading) {
      processFile(event.dataTransfer.files?.[0])
    }
  }

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-6 sm:py-8">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-zinc-100">
            Knowledge Sources
          </h1>
          <p className="mt-1 text-sm text-zinc-400">
            Your business documents in one place.
          </p>
        </div>

        <button
          type="button"
          onClick={handleAddSource}
          disabled={isUploading}
          className="flex shrink-0 items-center gap-2 rounded-lg bg-violet-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Plus size={16} />
          <span className="hidden sm:inline">Add source</span>
          <span className="sm:hidden">Add</span>
        </button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFileChange}
        className="hidden"
      />

      {error && (
        <p role="alert" className="mt-4 text-sm text-red-400">
          {error}
        </p>
      )}

      {success && (
        <p role="status" className="mt-4 text-sm text-emerald-400">
          {success}
        </p>
      )}

      {selectedFile ? (
        <div className="mt-8 flex flex-wrap items-center gap-3 border-b border-white/[0.08] py-4">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-violet-500/10">
            <FileText size={20} className="text-violet-400" />
          </div>

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-zinc-200">
              {selectedFile.name}
            </p>

            <p className="mt-1 text-xs text-zinc-500">
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              {' · '}Ready to upload
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
              className="flex items-center gap-2 rounded-lg bg-violet-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isUploading && (
                <span className="size-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              )}
              {isUploading ? 'Uploading...' : 'Upload PDF'}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-1 items-start justify-center pt-16 sm:pt-24">
          <div
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
            className={`flex w-full flex-col items-center rounded-xl border border-dashed px-5 py-12 text-center transition-colors sm:py-16 ${
              isDragging
                ? 'border-violet-400 bg-violet-500/10'
                : 'border-white/10 bg-white/[0.015]'
            }`}
          >
            <div className="mb-4 flex size-12 items-center justify-center rounded-xl bg-violet-500/10">
              <Upload size={22} className="text-violet-400" />
            </div>

            <h2 className="text-sm font-medium text-zinc-200">
              No documents selected
            </h2>

            <p className="mt-2 text-sm text-zinc-500">
              Add a PDF to your business knowledge base.
            </p>

            <button
              type="button"
              onClick={handleAddSource}
              className="mt-5 flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm font-medium text-zinc-300 transition hover:bg-white/[0.05] hover:text-white"
            >
              <Plus size={15} />
              Select PDF
            </button>

            <p className="mt-3 text-xs text-zinc-500">
              PDF files only · Maximum 10 MB
            </p>
            <p className="mt-1 text-xs text-zinc-600">
              or drag and drop a file here
            </p>
          </div>
        </div>
      )}
    </section>
  )
}

export default KnowledgeSourcesPage
