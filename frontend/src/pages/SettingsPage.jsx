
function SettingsPage() {
  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col overflow-y-auto px-4 py-6 sm:px-6 sm:py-8">
      <h1 className="text-xl font-semibold tracking-tight text-zinc-100">
        Settings
      </h1>

      <p className="mt-1 text-sm text-zinc-400">
        Manage your workspace preferences.
      </p>

      <div className="mt-8 border-b border-white/[0.08] pb-5">
        <h2 className="text-sm font-medium text-zinc-200">
          Workspace
        </h2>
        <p className="mt-1 text-sm text-zinc-500">
          My Workspace
        </p>
      </div>

      <div className="border-b border-white/[0.08] py-5">
        <h2 className="text-sm font-medium text-zinc-200">
          Account
        </h2>
        <p className="mt-1 text-sm text-zinc-500">
          Personal workspace
        </p>
      </div>
    </section>
  )
}

export default SettingsPage
