import { useState } from 'react'
import { Bot, Check, MessageSquare, RotateCcw, User } from 'lucide-react'

const DEFAULTS = {
  name: 'Knowvia Assistant',
  welcome: 'How can I help you today?',
  fallback: "I couldn't find that information in our business documents.",
}

const LIMITS = {
  name: 40,
  welcome: 200,
  fallback: 200,
}

const inputClass =
  'w-full rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5 text-sm text-white outline-none transition placeholder:text-zinc-600 focus:border-violet-400/50'

function Field({ id, label, hint, count, limit, children }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between gap-3">
        <label htmlFor={id} className="text-sm font-medium text-zinc-200">
          {label}
        </label>
        <span
          className={`text-xs ${
            count >= limit ? 'text-amber-400' : 'text-zinc-600'
          }`}
        >
          {count}/{limit}
        </span>
      </div>
      {children}
      {hint && <p className="mt-1.5 text-xs leading-5 text-zinc-500">{hint}</p>}
    </div>
  )
}

function AssistantSetupPage() {
  // UI only for now: values live in this page's state and are not saved
  // anywhere yet. Saving to the backend comes in a later step.
  const [values, setValues] = useState(DEFAULTS)
  const [saved, setSaved] = useState(DEFAULTS)
  const [justSaved, setJustSaved] = useState(false)

  const isDirty =
    values.name !== saved.name ||
    values.welcome !== saved.welcome ||
    values.fallback !== saved.fallback

  const nameMissing = values.name.trim() === ''
  const canSave = isDirty && !nameMissing

  function update(field, value) {
    setValues((current) => ({ ...current, [field]: value }))
    setJustSaved(false)
  }

  function handleSave() {
    if (!canSave) return
    setSaved(values)
    setJustSaved(true)
  }

  function handleReset() {
    setValues(DEFAULTS)
    setJustSaved(false)
  }

  const previewName = values.name.trim() || 'Your assistant'
  const previewWelcome = values.welcome.trim() || DEFAULTS.welcome
  const previewFallback = values.fallback.trim() || DEFAULTS.fallback

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 lg:px-8">
      {/* Header */}
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-lg font-medium tracking-tight text-zinc-100">
              Assistant Setup
            </h1>
            {isDirty && (
              <span className="rounded-full border border-amber-400/20 bg-amber-400/10 px-2.5 py-0.5 text-[11px] font-medium text-amber-300">
                Unsaved changes
              </span>
            )}
            {justSaved && !isDirty && (
              <span className="inline-flex items-center gap-1 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-0.5 text-[11px] font-medium text-emerald-300">
                <Check size={12} />
                Saved
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-zinc-500">
            Choose how your assistant introduces itself and replies.
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={handleReset}
            className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-2 text-xs text-zinc-400 transition hover:bg-white/[0.04] hover:text-zinc-100"
          >
            <RotateCcw size={13} />
            Reset
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!canSave}
            className="inline-flex items-center gap-1.5 rounded-lg bg-violet-600 px-3.5 py-2 text-xs font-medium text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-violet-600"
          >
            Save changes
          </button>
        </div>
      </header>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Form */}
        <div className="flex min-w-0 flex-col gap-4">
          <section className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
            <h2 className="text-sm font-medium text-zinc-200">Identity</h2>
            <p className="mt-0.5 text-xs text-zinc-500">
              The name customers see in the chat.
            </p>

            <div className="mt-4">
              <Field
                id="assistant-name"
                label="Assistant name"
                count={values.name.length}
                limit={LIMITS.name}
              >
                <input
                  id="assistant-name"
                  type="text"
                  value={values.name}
                  maxLength={LIMITS.name}
                  onChange={(event) => update('name', event.target.value)}
                  placeholder={DEFAULTS.name}
                  aria-invalid={nameMissing}
                  className={inputClass}
                />
              </Field>
              {nameMissing && (
                <p role="alert" className="mt-1.5 text-xs text-red-400">
                  Give your assistant a name.
                </p>
              )}
            </div>
          </section>

          <section className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
            <h2 className="text-sm font-medium text-zinc-200">Messages</h2>
            <p className="mt-0.5 text-xs text-zinc-500">
              What your assistant says at the start and when it cannot answer.
            </p>

            <div className="mt-4 space-y-5">
              <Field
                id="welcome-message"
                label="Welcome message"
                hint="Shown when a customer opens the chat."
                count={values.welcome.length}
                limit={LIMITS.welcome}
              >
                <textarea
                  id="welcome-message"
                  rows={3}
                  value={values.welcome}
                  maxLength={LIMITS.welcome}
                  onChange={(event) => update('welcome', event.target.value)}
                  placeholder={DEFAULTS.welcome}
                  className={`${inputClass} resize-y leading-6`}
                />
              </Field>

              <Field
                id="fallback-message"
                label="When an answer isn't found"
                hint="Sent when the documents do not contain the answer."
                count={values.fallback.length}
                limit={LIMITS.fallback}
              >
                <textarea
                  id="fallback-message"
                  rows={3}
                  value={values.fallback}
                  maxLength={LIMITS.fallback}
                  onChange={(event) => update('fallback', event.target.value)}
                  placeholder={DEFAULTS.fallback}
                  className={`${inputClass} resize-y leading-6`}
                />
              </Field>
            </div>
          </section>
        </div>

        {/* Live preview */}
        <aside className="min-w-0">
          <div className="rounded-xl border border-white/[0.08] bg-white/[0.02]">
            <div className="flex items-center gap-3 border-b border-white/[0.07] px-4 py-3">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-violet-600">
                <Bot size={18} />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-zinc-100">
                  {previewName}
                </p>
                <p className="text-[11px] text-zinc-500">Live preview</p>
              </div>
            </div>

            <div className="flex flex-col gap-4 p-4">
              {/* Welcome */}
              <div className="flex items-start gap-2.5">
                <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-violet-500/15 text-violet-200">
                  <Bot size={14} />
                </div>
                <p className="min-w-0 break-words rounded-2xl rounded-tl-sm bg-white/[0.05] px-3.5 py-2.5 text-sm leading-6 text-zinc-200">
                  {previewWelcome}
                </p>
              </div>

              {/* Sample customer question */}
              <div className="flex items-start justify-end gap-2.5">
                <p className="min-w-0 break-words rounded-2xl rounded-tr-sm bg-violet-600 px-3.5 py-2.5 text-sm leading-6 text-white">
                  Do you offer a night batch?
                </p>
                <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-white/[0.06] text-zinc-400">
                  <User size={14} />
                </div>
              </div>

              {/* Fallback */}
              <div className="flex items-start gap-2.5">
                <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-violet-500/15 text-violet-200">
                  <Bot size={14} />
                </div>
                <div className="min-w-0">
                  <p className="break-words rounded-2xl rounded-tl-sm bg-white/[0.05] px-3.5 py-2.5 text-sm leading-6 text-zinc-200">
                    {previewFallback}
                  </p>
                  <p className="mt-1 flex items-center gap-1 px-1 text-[11px] text-zinc-600">
                    <MessageSquare size={11} />
                    Shown when no answer is found
                  </p>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </section>
  )
}

export default AssistantSetupPage