import {
  AlertCircle,
  ArrowRight,
  Bot,
  Check,
  CheckCircle2,
  FileText,
  Files,
  Loader2,
  MessageSquare,
  Sparkles,
} from 'lucide-react'

// Placeholder data. Real values are wired in after the UI is approved.
// To preview the "new workspace" state, set documents to [].
const workspace = {
  documents: [
    { name: 'Course-Fees-2026.pdf', status: 'Processed', uploaded: '2 days ago' },
    { name: 'Refund-Policy.pdf', status: 'Processed', uploaded: '2 days ago' },
    { name: 'Class-Schedule.pdf', status: 'Processing', uploaded: 'Just now' },
  ],
  assistantConfigured: false,
  tested: false,
  lastTest: null,
}

const sampleQuestions = [
  'What is the refund policy?',
  'What are the course fees?',
  'When do classes start?',
]

const statusStyles = {
  Processed: {
    icon: CheckCircle2,
    className: 'text-emerald-400',
    spin: false,
  },
  Processing: {
    icon: Loader2,
    className: 'text-violet-300',
    spin: true,
  },
  Failed: {
    icon: AlertCircle,
    className: 'text-red-400',
    spin: false,
  },
}

function StatusBadge({ status }) {
  const style = statusStyles[status] ?? statusStyles.Processed
  const Icon = style.icon

  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 text-xs ${style.className}`}
    >
      <Icon size={13} className={style.spin ? 'animate-spin' : ''} />
      {status}
    </span>
  )
}

function OverviewPage({ onNavigate }) {
  const { documents, assistantConfigured, tested, lastTest } = workspace

  const hasDocuments = documents.length > 0
  const processedCount = documents.filter((d) => d.status === 'Processed').length
  const processingCount = documents.filter((d) => d.status === 'Processing').length
  const failedCount = documents.filter((d) => d.status === 'Failed').length

  let documentsNote = ''
  if (hasDocuments) {
    documentsNote = `${documents.length} uploaded`
    if (processingCount > 0) documentsNote += `, ${processingCount} processing`
    if (failedCount > 0) documentsNote += `, ${failedCount} failed`
  }

  const steps = [
    {
      title: 'Add your documents',
      description: 'Upload PDFs with fees, schedules, policies and FAQs.',
      doneNote: documentsNote,
      icon: Files,
      page: 'Knowledge Sources',
      cta: 'Upload',
      done: hasDocuments,
    },
    {
      title: 'Set up your assistant',
      description: 'Choose its name, welcome message and fallback reply.',
      doneNote: 'Configured',
      icon: Bot,
      page: 'Assistant Setup',
      cta: 'Set up',
      done: assistantConfigured,
    },
    {
      title: 'Test it with real questions',
      description: 'Ask what your customers ask and check the sources.',
      doneNote: lastTest ? `Last test: ${lastTest}` : 'Tested',
      icon: MessageSquare,
      page: 'Test Assistant',
      cta: 'Test',
      done: tested,
    },
  ]

  const doneCount = steps.filter((s) => s.done).length
  const allDone = doneCount === steps.length
  const nextStepIndex = steps.findIndex((s) => !s.done)
  const progressPercent = Math.round((doneCount / steps.length) * 100)

  let statusLabel = 'Ready'
  let statusClass = 'border-emerald-400/20 bg-emerald-400/10 text-emerald-300'

  if (processingCount > 0) {
    statusLabel = 'Processing'
    statusClass = 'border-violet-400/20 bg-violet-400/10 text-violet-200'
  } else if (!allDone) {
    statusLabel = 'Setup needed'
    statusClass = 'border-amber-400/20 bg-amber-400/10 text-amber-300'
  }

  const recentDocuments = documents.slice(0, 5)

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 lg:px-8">
      {/* Header */}
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-lg font-medium tracking-tight text-zinc-100">
              Overview
            </h1>
            <span
              className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${statusClass}`}
            >
              {statusLabel}
            </span>
          </div>
          <p className="mt-1 text-sm text-zinc-500">
            Is your assistant ready to answer customers?
          </p>
        </div>

        <button
          type="button"
          onClick={() => onNavigate('Test Assistant')}
          className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-violet-600 px-3.5 py-2 text-xs font-medium text-white transition hover:bg-violet-500"
        >
          <MessageSquare size={14} />
          Test assistant
        </button>
      </header>

      {/* What Knowvia does: only for a brand-new workspace */}
      {!hasDocuments && (
        <div className="mt-6 rounded-xl border border-violet-400/15 bg-violet-500/[0.06] p-4">
          <div className="flex items-start gap-3">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-violet-500/15 text-violet-200">
              <Sparkles size={17} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-zinc-100">
                Answers from your own documents
              </p>
              <p className="mt-1 text-xs leading-5 text-zinc-400">
                Upload your business PDFs. Knowvia answers customer questions
                from them and shows which document each answer came from.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Setup progress: replaced by the stat cards once everything is done */}
      {!allDone && (
        <section className="mt-6 rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-medium text-zinc-200">
                Get your assistant ready
              </h2>
              <p className="mt-0.5 text-xs text-zinc-500">
                {doneCount} of {steps.length} steps done
              </p>
            </div>
            <span className="text-xs text-zinc-500">{progressPercent}%</span>
          </div>

          <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06]">
            <div
              className="h-full rounded-full bg-violet-500 transition-all"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          <div className="mt-3">
            {steps.map((step, index) => {
              const Icon = step.icon
              const isNext = index === nextStepIndex

              return (
                <div
                  key={step.page}
                  className="flex items-center gap-3 border-b border-white/[0.06] py-3 last:border-b-0"
                >
                  <span
                    className={`flex size-8 shrink-0 items-center justify-center rounded-full ${
                      step.done
                        ? 'bg-emerald-400/15 text-emerald-300'
                        : isNext
                          ? 'bg-violet-500/15 text-violet-200'
                          : 'bg-white/[0.04] text-zinc-500'
                    }`}
                  >
                    {step.done ? <Check size={15} /> : <Icon size={15} />}
                  </span>

                  <div className="min-w-0 flex-1">
                    <p
                      className={`text-sm ${
                        step.done ? 'text-zinc-400' : 'text-zinc-200'
                      }`}
                    >
                      {step.title}
                    </p>
                    <p className="mt-0.5 text-xs leading-5 text-zinc-500">
                      {step.done ? step.doneNote : step.description}
                    </p>
                  </div>

                  {step.done ? (
                    <button
                      type="button"
                      onClick={() => onNavigate(step.page)}
                      className="shrink-0 text-xs text-zinc-500 transition hover:text-zinc-200"
                    >
                      View
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => onNavigate(step.page)}
                      className={`inline-flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs transition ${
                        isNext
                          ? 'bg-violet-600 font-medium text-white hover:bg-violet-500'
                          : 'border border-white/[0.1] text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100'
                      }`}
                    >
                      {step.cta}
                      <ArrowRight size={13} />
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Stats: only after setup is complete, so nothing repeats the checklist */}
      {allDone && (
        <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
            <div className="flex items-center gap-2 text-xs text-zinc-400">
              <Files size={15} />
              Documents
            </div>
            <p className="mt-3 text-2xl font-medium text-zinc-100">
              {documents.length}
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              {processedCount} ready
              {processingCount > 0 && `, ${processingCount} processing`}
              {failedCount > 0 && `, ${failedCount} failed`}
            </p>
          </div>

          <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
            <div className="flex items-center gap-2 text-xs text-zinc-400">
              <Bot size={15} />
              Assistant
            </div>
            <p className="mt-3 text-lg font-medium text-zinc-100">
              Configured
            </p>
            <button
              type="button"
              onClick={() => onNavigate('Assistant Setup')}
              className="mt-1 text-xs text-violet-300 transition hover:text-violet-200"
            >
              Edit setup
            </button>
          </div>

          <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
            <div className="flex items-center gap-2 text-xs text-zinc-400">
              <MessageSquare size={15} />
              Last test
            </div>
            <p className="mt-3 text-lg font-medium text-zinc-100">
              {lastTest ?? 'Tested'}
            </p>
            <button
              type="button"
              onClick={() => onNavigate('Test Assistant')}
              className="mt-1 text-xs text-violet-300 transition hover:text-violet-200"
            >
              Open Test Assistant
            </button>
          </div>
        </div>
      )}

      {/* Try it now + Recent documents */}
      {hasDocuments && (
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section>
            <h2 className="text-sm font-medium text-zinc-200">Try it now</h2>
            <p className="mt-1 text-xs text-zinc-500">
              Ask a question your customers might ask.
            </p>

            <div className="mt-3 flex flex-col gap-2">
              {sampleQuestions.map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => onNavigate('Test Assistant')}
                  className="group flex w-full items-center justify-between gap-3 rounded-xl border border-white/[0.08] px-4 py-3 text-left text-sm text-zinc-300 transition hover:border-violet-400/30 hover:bg-violet-500/[0.05] hover:text-white"
                >
                  <span className="min-w-0">{question}</span>
                  <ArrowRight
                    size={14}
                    className="shrink-0 text-zinc-600 transition group-hover:text-violet-300"
                  />
                </button>
              ))}
            </div>
          </section>

          <section>
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-medium text-zinc-200">
                  Recent documents
                </h2>
                <p className="mt-1 text-xs text-zinc-500">
                  Your latest knowledge sources.
                </p>
              </div>

              <button
                type="button"
                onClick={() => onNavigate('Uploaded Documents')}
                className="inline-flex shrink-0 items-center gap-1.5 text-xs text-zinc-400 transition hover:text-zinc-200"
              >
                View all
                <ArrowRight size={14} />
              </button>
            </div>

            <div className="mt-3 rounded-xl border border-white/[0.08] px-4">
              {recentDocuments.map((doc) => (
                <div
                  key={doc.name}
                  className="flex items-center gap-3 border-b border-white/[0.06] py-3 last:border-b-0"
                >
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-white/[0.04] text-zinc-400">
                    <FileText size={15} />
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm text-zinc-300">{doc.name}</p>
                    <p className="mt-0.5 text-xs text-zinc-500">
                      {doc.uploaded}
                    </p>
                  </div>

                  <StatusBadge status={doc.status} />
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </section>
  )
}

export default OverviewPage