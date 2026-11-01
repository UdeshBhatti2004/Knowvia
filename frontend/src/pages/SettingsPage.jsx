import { useEffect, useState } from 'react'
import { Building2, User, Save, RotateCcw } from 'lucide-react'

import { getMe, updateWorkspace } from '../services/api'

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

function SettingsPage() {
  const [me, setMe] = useState(null)
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState(null) // { type: 'ok' | 'error', text }

  useEffect(() => {
    getMe()
      .then((data) => {
        setMe(data)
        setName(data.workspace_name)
      })
      .catch(() => setStatus({ type: 'error', text: 'Could not load account.' }))
      .finally(() => setLoading(false))
  }, [])

  const isAdmin = Boolean(me?.is_admin)
  const unchanged = name.trim() === (me?.workspace_name || '')

  const handleReset = () => {
    setName(me?.workspace_name || '')
    setStatus(null)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (isAdmin || unchanged || !name.trim()) return

    setSaving(true)
    setStatus(null)
    try {
      const data = await updateWorkspace(name.trim())
      setMe((prev) => ({ ...prev, workspace_name: data.workspace_name }))
      setName(data.workspace_name)
      setStatus({ type: 'ok', text: 'Saved.' })
    } catch (err) {
      setStatus({ type: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

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
            <Field
              label="Workspace name"
              hint={isAdmin ? 'The admin account has no workspace to rename.' : undefined}
            >
              <input
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value)
                  setStatus(null)
                }}
                maxLength={100}
                disabled={loading || isAdmin}
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
                placeholder={isAdmin ? 'Admin login (no email)' : ''}
                className={inputClass}
              />
            </Field>
          </SectionCard>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={saving || loading || isAdmin || unchanged || !name.trim()}
            className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            {saving ? 'Saving...' : 'Save changes'}
          </button>
          <button
            type="button"
            onClick={handleReset}
            disabled={saving || loading || isAdmin || unchanged}
            className="inline-flex items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.02] px-4 py-2 text-sm font-medium text-zinc-300 transition-colors hover:bg-white/[0.05] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </button>
          {status && (
            <span
              className={`text-sm ${
                status.type === 'ok' ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {status.text}
            </span>
          )}
        </div>
      </form>
    </section>
  )
}

export default SettingsPage