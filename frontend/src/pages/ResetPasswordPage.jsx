import { useState } from 'react'
import {
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  Loader2,
} from 'lucide-react'
import { resetPassword } from '../services/api'
import PasswordInput from '../components/PasswordInput'

const inputBase =
  'w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 outline-none transition-colors focus:border-violet-500/60 focus:bg-white/[0.05]'

function goToSignIn() {
  window.location.assign('/')
}

function ResetPasswordPage() {
  const token = new URLSearchParams(window.location.search).get('token')

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  const ready = password.length >= 8 && confirm.length > 0

  async function handleSubmit(event) {
    event.preventDefault()
    if (!ready || submitting) return

    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }

    setSubmitting(true)
    setError('')

    try {
      await resetPassword(token, password)
      setDone(true)
    } catch (err) {
      setError(err.message || 'Could not reset password.')
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

        {done ? (
          <>
            <div
              role="status"
              className="mt-6 flex items-start gap-2 text-sm text-emerald-300"
            >
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              Password updated. You can sign in with your new password.
            </div>
            <button
              type="button"
              onClick={goToSignIn}
              className="mt-5 w-full rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-500"
            >
              Go to sign in
            </button>
          </>
        ) : !token ? (
          <>
            <div
              role="alert"
              className="mt-6 flex items-start gap-2 text-sm text-red-400"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              This reset link is invalid or has expired.
            </div>
            <button
              type="button"
              onClick={goToSignIn}
              className="mt-5 w-full rounded-lg border border-white/10 px-4 py-2 text-sm text-zinc-300 transition-colors hover:bg-white/[0.04]"
            >
              Back to sign in
            </button>
          </>
        ) : (
          <>
            <h1 className="mt-6 text-lg font-semibold text-zinc-100">
              Choose a new password
            </h1>
            <p className="mt-1 text-sm text-zinc-500">
              Use at least 8 characters.
            </p>

            <PasswordInput
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="New password"
              autoComplete="new-password"
              autoFocus
              maxLength={200}
              wrapperClassName="mt-5"
              className={inputBase}
            />

            <PasswordInput
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Confirm new password"
              autoComplete="new-password"
              maxLength={200}
              wrapperClassName="mt-3"
              className={inputBase}
            />

            {error && (
              <div
                role="alert"
                className="mt-3 flex items-start gap-2 text-sm text-red-400"
              >
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting || !ready}
              className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-500 disabled:opacity-40"
            >
              {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
              {submitting ? 'Please wait...' : 'Update password'}
            </button>

            <button
              type="button"
              onClick={goToSignIn}
              className="mt-4 text-left text-sm text-zinc-500 hover:text-zinc-300"
            >
              Back to sign in
            </button>
          </>
        )}
      </form>
    </div>
  )
}

export default ResetPasswordPage