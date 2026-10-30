import { useState } from 'react'
import { Building2, User, Save, RotateCcw } from 'lucide-react'

const DEFAULTS = {
  workspaceName: 'My Workspace',
  businessType: 'Tuition / Coaching',
  timezone: 'Asia/Kolkata',
  fullName: '',
  email: '',
}

const inputClass =
  'w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 outline-none transition-colors focus:border-violet-500/60 focus:bg-white/[0.05]'

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
  const [form, setForm] = useState(DEFAULTS)
  const [saved, setSaved] = useState(false)

  const update = (key) => (e) => {
    setForm((prev) => ({ ...prev, [key]: e.target.value }))
    setSaved(false)
  }

  const handleReset = () => {
    setForm(DEFAULTS)
    setSaved(false)
  }

  const handleSave = (e) => {
    e.preventDefault()
    setSaved(true)
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
            <Field label="Workspace name">
              <input
                type="text"
                value={form.workspaceName}
                onChange={update('workspaceName')}
                placeholder="e.g. Sunrise Tuition Classes"
                className={inputClass}
              />
            </Field>

            <Field label="Business type" hint="Helps tailor sample questions.">
              <input
                type="text"
                value={form.businessType}
                onChange={update('businessType')}
                placeholder="e.g. Coaching center, clinic, salon"
                className={inputClass}
              />
            </Field>

            <Field label="Timezone">
              <select
                value={form.timezone}
                onChange={update('timezone')}
                className={inputClass}
              >
                <option value="Asia/Kolkata">India (IST)</option>
                <option value="Asia/Dubai">Dubai (GST)</option>
                <option value="Europe/London">London (GMT/BST)</option>
                <option value="America/New_York">New York (ET)</option>
                <option value="America/Los_Angeles">Los Angeles (PT)</option>
              </select>
            </Field>
          </SectionCard>

          <SectionCard
            icon={User}
            title="Account"
            description="Your personal details."
          >
            <Field label="Full name">
              <input
                type="text"
                value={form.fullName}
                onChange={update('fullName')}
                placeholder="Your name"
                className={inputClass}
              />
            </Field>

            <Field
              label="Email"
              hint="Login and password come later with auth."
            >
              <input
                type="email"
                value={form.email}
                onChange={update('email')}
                placeholder="you@business.com"
                className={inputClass}
              />
            </Field>
          </SectionCard>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-500"
          >
            <Save className="h-4 w-4" />
            Save changes
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="inline-flex items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.02] px-4 py-2 text-sm font-medium text-zinc-300 transition-colors hover:bg-white/[0.05]"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </button>
          {saved && (
            <span className="text-sm text-zinc-500">
              Saved for this session only.
            </span>
          )}
        </div>
      </form>
    </section>
  )
}

export default SettingsPage