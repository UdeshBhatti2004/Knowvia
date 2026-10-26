
import { FileText, ExternalLink } from 'lucide-react'

function SourceReferences({ sources = [], source, page, similarity }) {
  const references =
    sources.length > 0
      ? sources
      : source
        ? [{ source, page, similarity }]
        : []

  if (references.length === 0) return null

  return (
    <div className="mt-5 border-t border-white/10 pt-4">
      <div className="mb-3 flex items-center gap-2">
        <FileText size={15} className="text-violet-300" />

        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Sources
        </h3>

        <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-zinc-500">
          {references.length}
        </span>
      </div>

      <div className="flex flex-col gap-2">
        {references.map((reference, index) => (
          <div
            key={`${reference.source}-${reference.page ?? index}-${index}`}
            className="flex items-center gap-3 rounded-xl border border-white/[0.07] bg-white/[0.02] p-3"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-500/10 text-violet-300">
              <FileText size={17} />
            </div>

            <div className="min-w-0 flex-1">
              <p className="break-all text-sm font-medium text-zinc-200">
                {reference.source}
              </p>

              <p className="mt-1 text-xs text-zinc-500">
                {reference.page != null
                  ? `Page ${reference.page}`
                  : 'Document reference'}
                {reference.similarity != null &&
                  ` · Similarity: ${(reference.similarity * 100).toFixed(1)}%`}
              </p>
            </div>

            <ExternalLink
              size={15}
              className="shrink-0 text-zinc-600"
            />
          </div>
        ))}
      </div>
    </div>
  )
}

export default SourceReferences
