
import { motion } from 'motion/react'
import { Bot, CheckCircle2 } from 'lucide-react'
import SourceReferences from './SourceReferences'

function AnswerCard({ result }) {
  if (!result) return null

  const hasSources =
    (Array.isArray(result.sources) && result.sources.length > 0) ||
    Boolean(result.source)

  const isFallback = !hasSources

  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="w-full rounded-2xl border border-white/10 bg-[#121216] p-5 sm:p-6"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-violet-500/10 text-violet-300">
          <Bot size={21} />
        </div>

        <div className="flex-1">
          <h2 className="text-sm font-semibold text-white">
            Knowvia AI
          </h2>

          <p className="mt-0.5 text-xs text-zinc-500">
            {isFallback
              ? 'Knowledge base response'
              : 'Answer generated from your knowledge base'}
          </p>
        </div>

        {!isFallback && (
          <span className="flex items-center gap-1.5 rounded-full border border-emerald-400/15 bg-emerald-400/5 px-2.5 py-1 text-xs text-emerald-300">
            <CheckCircle2 size={13} />
            Sources found
          </span>
        )}
      </div>

      <div className="mt-5 whitespace-pre-wrap break-words text-sm leading-7 text-zinc-300">
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
        <p className="mt-4 rounded-lg border border-amber-400/15 bg-amber-400/5 p-3 text-xs leading-5 text-amber-200/80">
          No relevant document source was found. Try rephrasing your
          question or asking about information in your uploaded documents.
        </p>
      )}
    </motion.article>
  )
}

export default AnswerCard
