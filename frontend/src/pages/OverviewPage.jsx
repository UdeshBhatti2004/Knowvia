
import {
  ArrowRight,
  Bot,
  FileText,
  Files,
  MessageSquare,
} from 'lucide-react'

function OverviewPage({ onNavigate }) {
  const setupSteps = [
    {
      title: 'Add knowledge sources',
      description: 'Upload documents about your business.',
      icon: Files,
      page: 'Knowledge Sources',
    },
    {
      title: 'Configure your assistant',
      description: 'Set its identity and welcome message.',
      icon: Bot,
      page: 'Assistant Setup',
    },
    {
      title: 'Test your assistant',
      description: 'Try asking questions about your business.',
      icon: MessageSquare,
      page: 'Test Assistant',
    },
  ]

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-5 sm:px-6 sm:py-6 lg:px-8">
      <header className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-medium tracking-tight text-zinc-100">
            Overview
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            Your business AI workspace at a glance.
          </p>
        </div>
      </header>

      {/* Workspace summary */}
      <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <Files size={15} />
            Knowledge sources
          </div>

          <p className="mt-3 text-lg font-medium text-zinc-100">
            Your knowledge base
          </p>

          <p className="mt-1 text-xs text-zinc-500">
            Documents that help your assistant answer questions.
          </p>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <Bot size={15} />
            Assistant
          </div>

          <p className="mt-3 text-lg font-medium text-zinc-100">
            Ready to configure
          </p>

          <p className="mt-1 text-xs text-zinc-500">
            Personalize your assistant before testing it.
          </p>
        </div>
      </div>

      {/* Recent documents */}
      <section className="mt-7">
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
            View history
            <ArrowRight size={14} />
          </button>
        </div>

        <div className="mt-3 flex items-center gap-3 rounded-xl border border-white/[0.08] px-4 py-4">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-white/[0.04] text-zinc-400">
            <FileText size={17} />
          </div>

          <div className="min-w-0 flex-1">
            <p className="text-sm text-zinc-300">
              Document activity
            </p>
            <p className="mt-1 text-xs leading-5 text-zinc-500">
              Open your document history to see uploaded files and their status.
            </p>
          </div>
        </div>
      </section>

      {/* Setup checklist */}
      <section className="mt-7">
        <div>
          <h2 className="text-sm font-medium text-zinc-200">
            Getting started
          </h2>
          <p className="mt-1 text-xs text-zinc-500">
            Set up your workspace in a few steps.
          </p>
        </div>

        <div className="mt-3 rounded-xl border border-white/[0.08] px-4">
          {setupSteps.map((step, index) => {
            const Icon = step.icon

            return (
              <button
                key={step.page}
                type="button"
                onClick={() => onNavigate(step.page)}
                className="group flex w-full items-center gap-3 border-b border-white/[0.06] py-3 text-left last:border-b-0"
              >
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-white/[0.04] text-zinc-400">
                  <Icon size={15} />
                </span>

                <span className="min-w-0 flex-1">
                  <span className="block text-sm text-zinc-300 transition group-hover:text-white">
                    {step.title}
                  </span>
                  <span className="mt-0.5 block text-xs leading-5 text-zinc-500">
                    {step.description}
                  </span>
                </span>

                {index === 0 ? (
                  <span className="shrink-0 text-xs text-zinc-500">
                    Start
                  </span>
                ) : (
                  <ArrowRight
                    size={14}
                    className="shrink-0 text-zinc-600 transition group-hover:text-zinc-300"
                  />
                )}
              </button>
            )
          })}
        </div>
      </section>
    </section>
  )
}

export default OverviewPage
