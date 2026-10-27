
import { useState } from 'react'
import { ArrowUp, Paperclip } from 'lucide-react'

function QuestionInput({
  value,
  onChange,
  onSubmit,
  isLoading = false,
}) {
  const [internalQuestion, setInternalQuestion] = useState('')

  const question = value ?? internalQuestion

  function updateQuestion(nextValue) {
    if (onChange) {
      onChange(nextValue)
    } else {
      setInternalQuestion(nextValue)
    }
  }

  function handleSubmit(event) {
  event.preventDefault()

  const trimmedQuestion = question.trim()

  if (!trimmedQuestion || isLoading) return

  onSubmit?.(trimmedQuestion)
}

function handleKeyDown(event) {
  const nativeEvent = event.nativeEvent
  if (nativeEvent.isComposing || nativeEvent.keyCode === 229) return

  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()

    if (!isLoading) {
      event.currentTarget.form?.requestSubmit()
    }
  }
}

  return (
    <form
      onSubmit={handleSubmit}
      className="overflow-hidden rounded-2xl border border-white/10 bg-[#171719] transition focus-within:border-violet-400/40"
    >
      <label htmlFor="knowvia-question" className="sr-only">
        Ask a question about your business
      </label>

      <textarea
        id="knowvia-question"
        value={question}
        onChange={(event) => updateQuestion(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything about your business..."
        rows={2}
        disabled={isLoading}
        className="block min-h-20 w-full resize-none bg-transparent px-4 py-4 text-sm leading-6 text-white outline-none placeholder:text-zinc-500 disabled:opacity-60 sm:min-h-24 sm:px-5"
      />

      <div className="flex items-center justify-between gap-2 px-3 pb-3 sm:px-4">
        <span className="hidden text-xs text-zinc-500 sm:block">
          Shift + Enter for a new line
        </span>

        <div className="ml-auto flex shrink-0 items-center gap-2">
          <button
            type="button"
            aria-label="Attach document"
            title="Document uploads coming soon"
            disabled
            className="flex h-9 w-9 items-center justify-center rounded-xl text-zinc-500 opacity-50"
          >
            <Paperclip size={17} />
          </button>

          <button
            type="submit"
            disabled={!question.trim() || isLoading}
            aria-label="Submit question"
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-600 text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isLoading ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            ) : (
              <ArrowUp size={18} />
            )}
          </button>
        </div>
      </div>
    </form>
  )
}

export default QuestionInput
