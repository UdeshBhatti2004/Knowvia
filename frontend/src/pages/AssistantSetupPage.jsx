
function AssistantSetupPage() {
  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-6 sm:py-8">
      <h1 className="text-xl font-semibold tracking-tight text-zinc-100">
        Assistant Setup
      </h1>

      <p className="mt-1 text-sm text-zinc-400">
        Configure how your assistant responds to customers.
      </p>

      <div className="mt-8 space-y-6">
        <div>
          <label
            htmlFor="assistant-name"
            className="mb-2 block text-sm font-medium text-zinc-200"
          >
            Assistant name
          </label>
          <input
            id="assistant-name"
            type="text"
            placeholder="Knowvia Assistant"
            className="w-full rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5 text-sm text-white outline-none placeholder:text-zinc-600 focus:border-violet-400/50 sm:w-3/4"
          />
        </div>

        <div>
          <label
            htmlFor="welcome-message"
            className="mb-2 block text-sm font-medium text-zinc-200"
          >
            Welcome message
          </label>
          <textarea
            id="welcome-message"
            rows={3}
            placeholder="How can I help you today?"
            className="w-full resize-y rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5 text-sm leading-6 text-white outline-none placeholder:text-zinc-600 focus:border-violet-400/50 sm:w-3/4"
          />
        </div>

        <div>
          <label
            htmlFor="fallback-message"
            className="mb-2 block text-sm font-medium text-zinc-200"
          >
            When an answer isn't found
          </label>
          <textarea
            id="fallback-message"
            rows={2}
            placeholder="I couldn't find that information in our business documents."
            className="w-full resize-y rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2.5 text-sm leading-6 text-white outline-none placeholder:text-zinc-600 focus:border-violet-400/50 sm:w-3/4"
          />
        </div>
      </div>
    </section>
  )
}

export default AssistantSetupPage
