
import { useState } from 'react'
import QuestionInput from '../components/chat/QuestionInput'
import AnswerCard from '../components/answers/AnswerCard'

const API_URL = 'http://127.0.0.1:8000'

const suggestions = [
  'What courses do we offer?',
  'What is our refund policy?',
  'How long is the Python course?',
]

function AskPage() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(value = question) {
    const submittedQuestion = value.trim()

    if (!submittedQuestion || isLoading) return

    setQuestion(submittedQuestion)
    setError('')
    setIsLoading(true)
    setResult(null)

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: submittedQuestion,
        }),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(
          data.detail || 'Unable to get an answer. Please try again.'
        )
      }

      setResult(data)
    } catch (err) {
      setError(
        err.message ||
          'Unable to connect to Knowvia. Check that the backend is running.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  function handleSuggestionClick(item) {
    setQuestion(item)
    setError('')
    handleSubmit(item)
  }

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
      <div className="flex min-h-0 flex-1 flex-col items-center justify-center overflow-y-auto px-4 py-8 sm:px-6">
        <div className="flex w-full flex-col gap-5 sm:w-4/5 lg:w-3/4">
          {!result && (
            <div className="text-center">
              <h1 className="text-2xl font-medium tracking-tight text-zinc-100 sm:text-3xl">
                What would you like to know?
              </h1>

              <p className="mt-2 text-sm text-zinc-400">
                Ask anything about your business.
              </p>
            </div>
          )}

          <QuestionInput
            value={question}
            onChange={(value) => {
              setQuestion(value)
              if (error) setError('')
            }}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />

          {!result && !isLoading && (
            <div className="flex flex-wrap justify-center gap-2">
              {suggestions.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => handleSuggestionClick(item)}
                  className="rounded-full border border-white/10 px-3 py-2 text-left text-xs leading-5 text-zinc-400 transition hover:border-white/20 hover:bg-white/[0.04] hover:text-zinc-200 sm:text-sm"
                >
                  {item}
                </button>
              ))}
            </div>
          )}

          {isLoading && (
            <p
              role="status"
              className="text-center text-sm text-zinc-400"
            >
              Searching your knowledge base...
            </p>
          )}

          {error && (
            <p
              role="alert"
              className="text-center text-sm text-amber-300"
            >
              {error}
            </p>
          )}

          {result && (
            <>
              <AnswerCard result={result} />

              <button
                type="button"
                onClick={() => {
                  setResult(null)
                  setError('')
                  setQuestion('')
                }}
                className="self-center rounded-lg border border-white/10 px-4 py-2 text-sm text-zinc-300 transition hover:bg-white/[0.05]"
              >
                Ask another question
              </button>
            </>
          )}
        </div>
      </div>
    </section>
  )
}

export default AskPage
