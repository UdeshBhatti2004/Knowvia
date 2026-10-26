
const suggestions = [
  'What courses do we offer?',
  'What is our refund policy?',
  'What is the Python course duration?',
]

function SuggestedQuestions({ onSelect }) {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs font-medium text-zinc-500">
        Suggested questions
      </p>

      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => onSelect?.(suggestion)}
            className="rounded-full border border-white/10 px-3 py-2 text-left text-xs leading-5 text-zinc-400 transition hover:border-violet-400/30 hover:bg-violet-500/[0.06] hover:text-zinc-100 sm:text-sm"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  )
}

export default SuggestedQuestions
