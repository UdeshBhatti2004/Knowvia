import { FileText } from 'lucide-react'

function SourceReferences({ sources = [], source, page, similarity }) {
  const references =
    sources.length > 0
      ? sources
      : source
        ? [{ source, page, similarity }]
        : []

  if (references.length === 0) return null

  return (
    <div className="mt-3 border-t border-white/[0.08] pt-3">
      <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
        Sources ({references.length})
      </p>

      <div className="flex flex-wrap gap-2">
        {references.map((reference, index) => (
          <div
            key={`${reference.source}-${reference.page ?? index}-${index}`}
            className="flex min-w-0 items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.03] px-2.5 py-1.5"
          >
            <FileText size={14} className="shrink-0 text-violet-300" />

            <div className="min-w-0">
              <p className="break-all text-xs font-medium text-zinc-200">
                {reference.source}
              </p>
              <p className="text-[11px] text-zinc-500">
                {reference.page != null
                  ? `Page ${reference.page}`
                  : 'Document reference'}
                {reference.similarity != null &&
                  ` \u00b7 ${(reference.similarity * 100).toFixed(0)}% match`}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SourceReferences