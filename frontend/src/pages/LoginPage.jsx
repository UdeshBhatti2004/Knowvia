import { useState } from 'react'
import {
  BrainCircuit,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react'
import { forgotPassword, login, signup } from '../services/api'
import PasswordInput from '../components/PasswordInput'

const inputBase =
  'w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 outline-none transition-colors focus:border-violet-500/60 focus:bg-white/[0.05]'
const inputClass = `mt-3 ${inputBase}`

function LoginPage({ onLoggedIn }) {
  // 'signin' | 'signup' | 'forgot'
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [workspaceName, setWorkspaceName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [resetSent, setResetSent] = useState(false)

  const isSignup = mode === 'signup'
  const isForgot = mode === 'forgot'
  const ready = isForgot
    ? Boolean(email.trim())
    : email.trim() && password && (!isSignup || workspaceName.trim())

  function switchMode(next) {
    setMode(next)
    setError('')
    setPassword('')
    setResetSent(false)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!ready || submitting) return

    setSubmitting(true)
    setError('')

    try {
      if (isForgot) {
        await forgotPassword(email.trim())
        setResetSent(true)
        return
      }

      if (isSignup) {
        await signup(email.trim(), password, workspaceName.trim())
      } else {
        await login(email.trim(), password)
      }
      onLoggedIn()
    } catch (err) {
      setError(err.message || 'Could not sign in.')
    } finally {
      setSubmitting(false)
    }
  }

  let title = 'Sign in'
  let subtitle = 'Sign in to open your dashboard.'
  let submitLabel = 'Sign in'

  if (isSignup) {
    title = 'Create your account'
    subtitle = 'Set up a workspace for your business.'
    submitLabel = 'Create account'
  } else if (isForgot) {
    title = 'Reset your password'
    subtitle = "Enter your email and we'll send you a reset link."
    submitLabel = 'Send reset link'
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

        <h1 className="mt-6 text-lg font-semibold text-zinc-100">{title}</h1>
        <p className="mt-1 text-sm text-zinc-500">{subtitle}</p>

        {isSignup && (
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

        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          autoComplete="email"
          autoFocus={!isSignup}
          disabled={resetSent}
          className={isSignup ? inputClass : `${inputClass} mt-5`}
        />

        {!isForgot && (
          <PasswordInput
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={isSignup ? 'Password (8+ characters)' : 'Password'}
            autoComplete={isSignup ? 'new-password' : 'current-password'}
            maxLength={200}
            wrapperClassName="mt-3"
            className={inputBase}
          />
        )}

        {mode === 'signin' && (
          <button
            type="button"
            onClick={() => switchMode('forgot')}
            className="mt-2 text-left text-xs text-zinc-500 hover:text-zinc-300"
          >
            Forgot password?
          </button>
        )}

        {resetSent && (
          <div
            role="status"
            className="mt-3 flex items-start gap-2 text-sm text-emerald-300"
          >
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
            If an account exists for that email, a reset link is on its way.
            It is valid for 1 hour.
          </div>
        )}

        {error && (
          <div className="mt-3 flex items-center gap-2 text-sm text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {!resetSent && (
          <button
            type="submit"
            disabled={submitting || !ready}
            className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-500 disabled:opacity-40"
          >
            {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {submitting ? 'Please wait...' : submitLabel}
          </button>
        )}

        <div className="mt-4 text-sm text-zinc-500">
          {isForgot ? (
            <button
              type="button"
              onClick={() => switchMode('signin')}
              className="text-left hover:text-zinc-300"
            >
              Back to sign in
            </button>
          ) : (
            <button
              type="button"
              onClick={() => switchMode(isSignup ? 'signin' : 'signup')}
              className="text-left hover:text-zinc-300"
            >
              {isSignup
                ? 'Already have an account? Sign in'
                : 'New here? Create an account'}
            </button>
          )}
        </div>
      </form>
    </div>
  )
}

export default LoginPage