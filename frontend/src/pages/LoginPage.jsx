import { useState } from 'react'
import { BrainCircuit, Loader2, AlertCircle } from 'lucide-react'
import { login, signup } from '../services/api'

const inputClass =
  'mt-3 w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 outline-none transition-colors focus:border-violet-500/60 focus:bg-white/[0.05]'

function LoginPage({ onLoggedIn }) {
  // 'signin' | 'signup' | 'admin'
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [workspaceName, setWorkspaceName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const ready =
    password &&
    (mode === 'admin' || email.trim()) &&
    (mode !== 'signup' || workspaceName.trim())

  function switchMode(next) {
    setMode(next)
    setError('')
    setPassword('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!ready || submitting) return

    setSubmitting(true)
    setError('')

    try {
      if (mode === 'signup') {
        await signup(email.trim(), password, workspaceName.trim())
      } else if (mode === 'signin') {
        await login(password, email.trim())
      } else {
        await login(password)
      }
      onLoggedIn()
    } catch (err) {
      setError(err.message || 'Could not sign in.')
    } finally {
      setSubmitting(false)
    }
  }

  const title =
    mode === 'signup'
      ? 'Create your account'
      : mode === 'admin'
        ? 'Admin sign in'
        : 'Sign in'

  const subtitle =
    mode === 'signup'
      ? 'Set up a workspace for your business.'
      : mode === 'admin'
        ? 'Enter the admin password to open the dashboard.'
        : 'Sign in to open your dashboard.'

  const submitLabel =
    mode === 'signup' ? 'Create account' : 'Sign in'

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

        <h1 className="mt-6 text-lg font-semibold text-zinc-100">{title}</h1>
        <p className="mt-1 text-sm text-zinc-500">{subtitle}</p>

        {mode === 'signup' && (
          <input
            type="text"
            value={workspaceName}
            onChange={(e) => setWorkspaceName(e.target.value)}
            placeholder="Business name"
            maxLength={100}
            autoFocus
            className={`${inputClass} mt-5`}
          />
        )}

        {mode !== 'admin' && (
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            autoComplete="email"
            autoFocus={mode === 'signin'}
            className={mode === 'signup' ? inputClass : `${inputClass} mt-5`}
          />
        )}

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder={mode === 'signup' ? 'Password (8+ characters)' : 'Password'}
          autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
          autoFocus={mode === 'admin'}
          className={mode === 'admin' ? `${inputClass} mt-5` : inputClass}
        />

        {error && (
          <div className="mt-3 flex items-center gap-2 text-sm text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || !ready}
          className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-500 disabled:opacity-40"
        >
          {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
          {submitting ? 'Please wait...' : submitLabel}
        </button>

        <div className="mt-4 flex flex-col gap-1.5 text-sm text-zinc-500">
          {mode === 'signup' ? (
            <button
              type="button"
              onClick={() => switchMode('signin')}
              className="text-left hover:text-zinc-300"
            >
              Already have an account? Sign in
            </button>
          ) : (
            <button
              type="button"
              onClick={() => switchMode('signup')}
              className="text-left hover:text-zinc-300"
            >
              New here? Create an account
            </button>
          )}

          {mode === 'admin' ? (
            <button
              type="button"
              onClick={() => switchMode('signin')}
              className="text-left hover:text-zinc-300"
            >
              Back to email sign in
            </button>
          ) : (
            <button
              type="button"
              onClick={() => switchMode('admin')}
              className="text-left text-xs text-zinc-600 hover:text-zinc-400"
            >
              Sign in with admin password
            </button>
          )}
        </div>
      </form>
    </div>
  )
}

export default LoginPage