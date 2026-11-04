import { useEffect, useState } from 'react'
import {
  Code,
  Copy,
  Check,
  Loader2,
  AlertCircle,
  Globe,
  Save,
  Link2,
  ExternalLink,
} from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { API_URL, apiFetch } from '../services/api'
import {
  WIDGET_DOMAINS_KEY,
  useWidget,
  useWidgetDomains,
} from '../hooks/useWidget'

function InstallPage() {

  const queryClient = useQueryClient()
  const widgetQuery = useWidget()
  const domainsQuery = useWidgetDomains()

  const publicKey = widgetQuery.data?.public_key || ''
  const loading = widgetQuery.isLoading
  const domainsLoading = domainsQuery.isLoading

  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [linkCopied, setLinkCopied] = useState(false)

  // Start from the cached domains so there is no empty-box flash on revisit.
  const cachedDomains = domainsQuery.data
    ? domainsQuery.data.domains.join('\n')
    : ''
  const [domainsText, setDomainsText] = useState(cachedDomains)
  const [savedDomainsText, setSavedDomainsText] = useState(cachedDomains)
  const [domainsSaving, setDomainsSaving] = useState(false)
  const [domainsError, setDomainsError] = useState('')
  const [domainsSaved, setDomainsSaved] = useState(false)

  // Fill the box when domains load or change in the cache.
  useEffect(() => {
    if (!domainsQuery.data) return
    const text = domainsQuery.data.domains.join('\n')
    setDomainsText(text)
    setSavedDomainsText(text)
  }, [domainsQuery.data])

  // Show load errors only when there is nothing cached.
  useEffect(() => {
    if (widgetQuery.isError && !widgetQuery.data) {
      setError('Could not load your widget key. Is the backend running?')
    }
  }, [widgetQuery.isError, widgetQuery.data])

  useEffect(() => {
    if (domainsQuery.isError && !domainsQuery.data) {
      setDomainsError('Could not load allowed domains.')
    }
  }, [domainsQuery.isError, domainsQuery.data])

  const snippet = `<script src="${window.location.origin}/widget.js" data-key="${publicKey}"></script>`
  const shareLink = `${window.location.origin}/chat?key=${encodeURIComponent(publicKey)}`

  async function copyText(text, setFlag) {
    try {
      await navigator.clipboard.writeText(text)
      setFlag(true)
      setTimeout(() => setFlag(false), 2000)
    } catch {
      setError('Copy failed. Select the text and copy it manually.')
    }
  }

  async function handleSaveDomains() {
    setDomainsSaving(true)
    setDomainsError('')
    setDomainsSaved(false)

    const domains = domainsText
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)

    try {
      const response = await apiFetch(`${API_URL}/widget/domains`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domains }),
      })

      if (!response.ok) {
        let message = 'Could not save domains.'
        try {
          const body = await response.json()
          if (typeof body.detail === 'string') message = body.detail
          else if (Array.isArray(body.detail))
            message = 'Too many domains (max 20).'
        } catch {
          // keep default message
        }
        throw new Error(message)
      }

      const data = await response.json()
      const text = data.domains.join('\n')
      queryClient.setQueryData(WIDGET_DOMAINS_KEY, data)
      setDomainsText(text)
      setSavedDomainsText(text)
      setDomainsSaved(true)
      setTimeout(() => setDomainsSaved(false), 2500)
    } catch (err) {
      setDomainsError(err.message || 'Could not save domains.')
    } finally {
      setDomainsSaving(false)
    }
  }

  const domainsChanged = domainsText !== savedDomainsText

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 lg:px-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-zinc-100">
          Install
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Give your customers the assistant: share a link, or add it to your
          website.
        </p>
      </div>

      <div className="mt-6 flex w-full flex-col gap-5 xl:w-3/4">
        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-violet-500/20 bg-violet-500/10 text-violet-300">
              <Link2 className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-zinc-100">
                Share link
              </h2>
              <p className="mt-0.5 text-sm text-zinc-500">
                No website needed. Send this link on WhatsApp, Instagram, email
                or print it as a QR code. Customers open it and chat.
              </p>
            </div>
          </div>

          <div className="mt-5">
            {loading && (
              <div className="flex items-center gap-2 text-sm text-zinc-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading...
              </div>
            )}

            {!loading && publicKey && (
              <div className="rounded-lg border border-white/[0.08] bg-black/30">
                <div className="flex items-center justify-between gap-2 border-b border-white/[0.06] px-3 py-2">
                  <span className="text-xs text-zinc-500">Link</span>
                  <div className="flex items-center gap-2">
                    <a
                      href={shareLink}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-white/[0.03] px-2.5 py-1 text-xs font-medium text-zinc-300 transition-colors hover:bg-white/[0.07]"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      Open
                    </a>
                    <button
                      type="button"
                      onClick={() => copyText(shareLink, setLinkCopied)}
                      className="inline-flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-white/[0.03] px-2.5 py-1 text-xs font-medium text-zinc-300 transition-colors hover:bg-white/[0.07]"
                    >
                      {linkCopied ? (
                        <Check className="h-3.5 w-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                      {linkCopied ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                </div>
                <p className="break-all p-3 text-xs leading-relaxed text-zinc-200">
                  {shareLink}
                </p>
              </div>
            )}
          </div>

          <p className="mt-4 text-xs text-zinc-500">
            Anyone with this link can ask questions. They cannot see or change
            your documents or settings.
          </p>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-violet-500/20 bg-violet-500/10 text-violet-300">
              <Code className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-zinc-100">
                Embed on your website
              </h2>
              <p className="mt-0.5 text-sm text-zinc-500">
                Paste this just before the closing &lt;/body&gt; tag on every
                page where you want the chat bubble.
              </p>
            </div>
          </div>

          <div className="mt-5">
            {loading && (
              <div className="flex items-center gap-2 text-sm text-zinc-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading...
              </div>
            )}

            {!loading && publicKey && (
              <div className="rounded-lg border border-white/[0.08] bg-black/30">
                <div className="flex items-center justify-between border-b border-white/[0.06] px-3 py-2">
                  <span className="text-xs text-zinc-500">HTML</span>
                  <button
                    type="button"
                    onClick={() => copyText(snippet, setCopied)}
                    className="inline-flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-white/[0.03] px-2.5 py-1 text-xs font-medium text-zinc-300 transition-colors hover:bg-white/[0.07]"
                  >
                    {copied ? (
                      <Check className="h-3.5 w-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="h-3.5 w-3.5" />
                    )}
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <pre className="overflow-x-auto whitespace-pre-wrap break-all p-3 text-xs leading-relaxed text-zinc-200">
                  {snippet}
                </pre>
              </div>
            )}

            {error && (
              <div className="mt-3 flex items-center gap-2 text-sm text-red-400">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}
          </div>

          <p className="mt-4 text-xs text-zinc-500">
            The key is public by design. Visitors can only ask questions; they
            cannot see or change your documents or settings.
          </p>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-violet-500/20 bg-violet-500/10 text-violet-300">
              <Globe className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-zinc-100">
                Allowed domains
              </h2>
              <p className="mt-0.5 text-sm text-zinc-500">
                Only these websites can show your chat bubble. Leave empty to
                allow any website. This does not affect the share link above.
              </p>
            </div>
          </div>

          <div className="mt-5">
            {domainsLoading ? (
              <div className="flex items-center gap-2 text-sm text-zinc-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading...
              </div>
            ) : (
              <>
                <textarea
                  value={domainsText}
                  onChange={(e) => {
                    setDomainsText(e.target.value)
                    setDomainsSaved(false)
                  }}
                  rows={5}
                  spellCheck={false}
                  placeholder={'example.com\n*.example.com'}
                  className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 font-mono text-sm text-zinc-100 placeholder:text-zinc-600 outline-none transition-colors focus:border-violet-500/60 focus:bg-white/[0.05]"
                />
                <p className="mt-1.5 text-xs text-zinc-500">
                  One domain per line. Use *.example.com to include
                  subdomains. Max 20.
                </p>
              </>
            )}

            {domainsError && (
              <div className="mt-3 flex items-center gap-2 text-sm text-red-400">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {domainsError}
              </div>
            )}

            <div className="mt-4 flex items-center gap-3">
              <button
                type="button"
                onClick={handleSaveDomains}
                disabled={domainsLoading || domainsSaving || !domainsChanged}
                className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-500 disabled:opacity-40"
              >
                {domainsSaving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                {domainsSaving ? 'Saving...' : 'Save domains'}
              </button>
              {domainsSaved && (
                <span className="inline-flex items-center gap-1.5 text-sm text-emerald-400">
                  <Check className="h-4 w-4" />
                  Saved
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default InstallPage