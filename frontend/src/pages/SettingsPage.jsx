import { useEffect, useState } from 'react'
import { Building2, User, Save, RotateCcw, KeyRound } from 'lucide-react'

import { changePassword, updateWorkspace } from '../services/api'
import { useMe, useRefreshMe } from '../hooks/useMe'
import PasswordInput from '../components/PasswordInput'

const inputClass =
  'w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 outline-none transition-colors focus:border-violet-500/60 focus:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-60'

function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-zinc-200">{label}</span>
      {hint && <span className="mt-0.5 block text-xs text-zinc-500">{hint}</span>}
      <div className="mt-2">{children}</div>
    </label>
  )
}

function SectionCard({ icon: Icon, title, description, children }) {
  return (
    <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-violet-500/20 bg-violet-500/10 text-violet-300">
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-zinc-100">{title}</h2>
          <p className="mt-0.5 text-sm text-zinc-500">{description}</p>
        </div>
      </div>
      <div className="mt-5 space-y-4">{children}</div>
    </div>
  )
}

function StatusText({ status }) {
  if (!status) return null
  return (
    <span
      className={`text-sm ${
        status.type === 'ok' ? 'text-emerald-400' : 'text-red-400'
      }`}
    >
      {status.text}
    </span>
  )
}

function Hint({ show, children }) {
  if (!show) return null
  return <p className="mt-1.5 text-xs text-red-400">{children}</p>
}

function SettingsPage() {
  const { data: me, isLoading: loading, isError } = useMe()
  const refreshMe = useRefreshMe()
  const [name, setName] = useState(me?.workspace_name || '')
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState(null) // { type: 'ok' | 'error', text }

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [changingPassword, setChangingPassword] = useState(false)
  const [passwordStatus, setPasswordStatus] = useState(null)

  // Fill the field when the account loads (cached or fresh).
  const loadedName = me?.workspace_name
  useEffect(() => {
    if (loadedName !== undefined) setName(loadedName)
  }, [loadedName])

  const shownStatus =
    status ||
    (isError && !me
      ? { type: 'error', text: 'Could not load account.' }
      : null)

  const unchanged = name.trim() === (me?.workspace_name || '')

  const handleReset = () => {
    setName(me?.workspace_name || '')
    setStatus(null)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (unchanged || !name.trim()) return

    setSaving(true)
    setStatus(null)
    try {
      const data = await updateWorkspace(name.trim())
      setName(data.workspace_name)
      refreshMe()
      setStatus({ type: 'ok', text: 'Saved.' })
    } catch (err) {
      setStatus({ type: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  const passwordReady =
    currentPassword.length > 0 &&
    newPassword.length > 0 &&
    confirmPassword.length > 0

  const newTooShort = newPassword.length > 0 && newPassword.length < 8
  const mismatch = confirmPassword.length > 0 && newPassword !== confirmPassword
  const sameAsCurrent =
    newPassword.length > 0 && newPassword === currentPassword

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    if (!passwordReady || newTooShort || mismatch || sameAsCurrent) return

    setChangingPassword(true)
    setPasswordStatus(null)
    try {
      await changePassword(currentPassword, newPassword)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setPasswordStatus({ type: 'ok', text: 'Password changed.' })
    } catch (err) {
      setPasswordStatus({ type: 'error', text: err.message })
    } finally {
      setChangingPassword(false)
    }
  }

  const clearPasswordStatus = () => setPasswordStatus(null)

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 lg:px-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-zinc-100">
          Settings
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Manage your workspace and account details.
        </p>
      </div>

      <form onSubmit={handleSave} className="mt-6 flex flex-col gap-5">
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          <SectionCard
            icon={Building2}
            title="Workspace"
            description="How your business appears in Knowvia."
          >
            <Field label="Workspace name">
              <input
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value)
                  setStatus(null)
                }}
                maxLength={100}
                disabled={loading}
                placeholder="e.g. Sunrise Tuition Classes"
                className={inputClass}
              />
            </Field>
          </SectionCard>

          <SectionCard
            icon={User}
            title="Account"
            description="Your login details."
          >
            <Field label="Email" hint="Can't be changed yet.">
              <input
                type="email"
                value={me?.email || ''}
                readOnly
                disabled
                className={inputClass}
              />
            </Field>
          </SectionCard>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={saving || loading || unchanged || !name.trim()}
            className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            {saving ? 'Saving...' : 'Save changes'}
          </button>
          <button
            type="button"
            onClick={handleReset}
            disabled={saving || loading || unchanged}
            className="inline-flex items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.02] px-4 py-2 text-sm font-medium text-zinc-300 transition-colors hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </button>
          <StatusText status={shownStatus} />
        </div>
      </form>

      <form
        onSubmit={handlePasswordChange}
        className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-2"
      >
        <SectionCard
          icon={KeyRound}
          title="Password"
          description="New password needs at least 8 characters."
        >
          <Field label="Current password">
            <PasswordInput
              value={currentPassword}
              onChange={(e) => {
                setCurrentPassword(e.target.value)
                clearPasswordStatus()
              }}
              autoComplete="current-password"
              maxLength={200}
              className={inputClass}
            />
          </Field>
          <Field label="New password">
            <PasswordInput
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value)
                clearPasswordStatus()
              }}
              autoComplete="new-password"
              maxLength={200}
              className={inputClass}
            />
            <Hint show={newTooShort}>
              Too short: {newPassword.length}/8 characters.
            </Hint>
            <Hint show={sameAsCurrent}>
              New password must be different from the current one.
            </Hint>
          </Field>
          <Field label="Confirm new password">
            <PasswordInput
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value)
                clearPasswordStatus()
              }}
              autoComplete="new-password"
              maxLength={200}
              className={inputClass}
            />
            <Hint show={mismatch}>Passwords don't match.</Hint>
          </Field>
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={
                changingPassword ||
                !passwordReady ||
                newTooShort ||
                mismatch ||
                sameAsCurrent
              }
              className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <KeyRound className="h-4 w-4" />
              {changingPassword ? 'Changing...' : 'Change password'}
            </button>
            <StatusText status={passwordStatus} />
          </div>
        </SectionCard>
      </form>
    </section>
  )
}

export default SettingsPage