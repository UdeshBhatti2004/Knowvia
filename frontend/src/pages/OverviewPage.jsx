
import {  Files, MessageSquare } from 'lucide-react'

function OverviewPage({ onNavigate }) {
  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-6 sm:py-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-zinc-100">
          Overview
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Your business AI workspace at a glance.
        </p>
      </div>

      <div className="mt-8 flex flex-col gap-4 sm:flex-row">
        <div className="flex items-center gap-3 border-b border-white/[0.08] pb-4 sm:flex-1 sm:border-b-0">
          <Files size={19} className="text-zinc-400" />
          <div>
            <p className="text-sm text-zinc-300">Knowledge sources</p>
            <p className="mt-1 text-xs text-zinc-500">No documents yet</p>
          </div>
        </div>

        <div className="flex items-center gap-3 pb-2 sm:flex-1">
          <MessageSquare size={19} className="text-zinc-400" />
          <div>
            <p className="text-sm text-zinc-300">Assistant</p>
            <p className="mt-1 text-xs text-zinc-500">Ready to configure</p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default OverviewPage
