import { useState } from 'react'
import { BrainCircuit, Loader2, AlertCircle } from 'lucide-react'
import { login } from '../services/api'

function LoginPage({ onLoggedIn }) {
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    if (!password || submitting) return

    setSubmitting(true)
    setError('')

    try {
      await login(password)
      onLoggedIn()
    } catch (err) {
      setError(err.message || 'Could not sign in.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex h-dvh w-full items-center justify-center bg-[#0a0a0c] p-4">
      <form
        onSubmit={handleSubmit}
        className="w-11/12 rounded-xl border border-white/[0.08] bg-white/[0.02] p-6 sm:w-96"
      >
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-600 text-white">
            <BrainCircuit size={21} />
          </div>
          <div>
            <p className="text-base font-semibold tracking-tight text-white">
              knowvia
            </p>
            <p className="text-[11px] text-zinc-500">Business AI</p>
          </div>
        </div>

        <h1 className="mt-6 text-lg font-semibold text-zinc-100">Sign in</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Enter the admin password to open your dashboard.
        </p>

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          autoFocus
          className="mt-5 w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 outline-none transition-colors focus:border-violet-500/60 focus:bg-white/[0.05]"
        />

        {error && (
          <div className="mt-3 flex items-center gap-2 text-sm text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || !password}
          className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-500 disabled:opacity-40"
        >
          {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
          {submitting ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}

export default LoginPage