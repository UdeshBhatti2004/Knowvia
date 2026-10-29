import { motion } from 'motion/react'
import { AlertCircle } from 'lucide-react'
import SourceReferences from './SourceReferences'

function AnswerCard({ result }) {
  if (!result) return null

  const hasSources =
    (Array.isArray(result.sources) && result.sources.length > 0) ||
    Boolean(result.source)

  return (
    <motion.article
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="rounded-2xl rounded-tl-sm bg-white/[0.05] px-4 py-3"
    >
      <div className="whitespace-pre-wrap break-words text-sm leading-7 text-zinc-200">
        {result.answer || 'No answer was returned.'}
      </div>

      {hasSources ? (
        <SourceReferences
          sources={result.sources}
          source={result.source}
          page={result.page}
          similarity={result.similarity}
        />
      ) : (
        <p className="mt-3 flex items-start gap-2 rounded-lg border border-amber-400/15 bg-amber-400/5 p-2.5 text-xs leading-5 text-amber-200/80">
          <AlertCircle size={14} className="mt-0.5 shrink-0" />
          No matching source in your documents. Try rephrasing, or add a
          document that covers this.
        </p>
      )}
    </motion.article>
  )
}

export default AnswerCard