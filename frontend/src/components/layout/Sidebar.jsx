
import {
  BrainCircuit,
  LayoutDashboard,
  Files,
  MessageSquare,
  SlidersHorizontal,
  Settings2,
  Plus,
  PanelLeftClose,
  PanelLeftOpen,
  X,
  FileText,
} from 'lucide-react'


const navigationItems = [
  { label: 'Overview', icon: LayoutDashboard },
  { label: 'Knowledge Sources', icon: Files },
  { label: 'Uploaded Documents', icon: FileText },
  { label: 'Test Assistant', icon: MessageSquare },
  { label: 'Assistant Setup', icon: SlidersHorizontal },
]


function Sidebar({
  isOpen,
  onClose,
  isCollapsed,
  onToggleCollapse,
  activePage = 'Test Assistant',
  onNavigate,
}) {
  function handleNavigate(label) {
    onNavigate?.(label)
    onClose?.()
  }

  return (
    <>
      {isOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex h-screen shrink-0 flex-col border-r border-white/[0.08] bg-[#111114] text-white transition-[width,transform] duration-200 lg:sticky lg:top-0 lg:z-20 ${
          isOpen
            ? 'translate-x-0'
            : '-translate-x-full invisible lg:translate-x-0 lg:visible'
        } ${isCollapsed ? 'lg:w-[68px]' : 'lg:w-[260px] w-[260px]'}`}
      >
        <div
          className={`flex h-14 shrink-0 items-center border-b border-white/[0.07] ${
            isCollapsed ? 'justify-center px-1' : 'justify-between px-3'
          }`}
        >
          <div className="flex min-w-0 items-center gap-2.5">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-600">
              <BrainCircuit size={21} />
            </div>

            {!isCollapsed && (
              <div className="min-w-0">
                <p className="text-base font-semibold tracking-tight">
                  knowvia
                </p>
                <p className="text-[11px] text-zinc-500">Business AI</p>
              </div>
            )}
          </div>

          {!isCollapsed && (
            <button
              type="button"
              onClick={onToggleCollapse}
              aria-label="Collapse sidebar"
              title="Collapse sidebar"
              className="hidden h-8 w-8 shrink-0 items-center justify-center rounded-lg text-zinc-500 transition hover:bg-white/[0.06] hover:text-white lg:flex"
            >
              <PanelLeftClose size={17} />
            </button>
          )}

          <button
            type="button"
            onClick={onClose}
            aria-label="Close sidebar"
            className="rounded-lg p-2 text-zinc-400 hover:bg-white/5 lg:hidden"
          >
            <X size={19} />
          </button>
        </div>

        <div className="shrink-0 p-2.5">
          <button
            type="button"
            title={isCollapsed ? 'My Workspace' : undefined}
            className={`flex w-full items-center rounded-lg border border-white/[0.07] p-2 transition hover:bg-white/[0.04] ${
              isCollapsed ? 'justify-center' : 'gap-2.5'
            }`}
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-violet-500/15 text-sm text-violet-200">
              W
            </div>

            {!isCollapsed && (
              <>
                <div className="min-w-0 flex-1 text-left">
                  <p className="truncate text-xs font-medium">
                    My Workspace
                  </p>
                  <p className="mt-0.5 text-[11px] text-zinc-500">
                    Free plan
                  </p>
                </div>
                <Plus size={15} className="text-zinc-500" />
              </>
            )}
          </button>
        </div>

        <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto px-2.5">
          {!isCollapsed && (
            <p className="mb-2 px-2 text-[10px] font-medium tracking-widest text-zinc-600">
              WORKSPACE
            </p>
          )}

          {navigationItems.map(({ label, icon: Icon }) => {
            const isActive = activePage === label

            return (
              <button
                key={label}
                type="button"
                title={isCollapsed ? label : undefined}
                aria-current={isActive ? 'page' : undefined}
                onClick={() => handleNavigate(label)}
                className={`flex w-full items-center rounded-lg py-2.5 text-xs transition ${
                  isCollapsed ? 'justify-center px-1' : 'gap-2.5 px-2.5'
                } ${
                  isActive
                    ? 'bg-violet-500/10 font-medium text-violet-200'
                    : 'text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100'
                }`}
              >
                <Icon size={17} className="shrink-0" />
                {!isCollapsed && <span>{label}</span>}
              </button>
            )
          })}
        </nav>

        <div className="mt-auto shrink-0 border-t border-white/[0.07] p-2.5">
          <button
            type="button"
            title={isCollapsed ? 'Settings' : undefined}
            onClick={() => handleNavigate('Settings')}
            className={`flex w-full items-center rounded-lg py-2.5 text-xs transition hover:bg-white/[0.04] hover:text-white ${
              isCollapsed
                ? 'justify-center px-1'
                : 'gap-2.5 px-2.5'
            } ${
              activePage === 'Settings'
                ? 'text-violet-200'
                : 'text-zinc-400'
            }`}
          >
            <Settings2 size={17} />
            {!isCollapsed && <span>Settings</span>}
          </button>

          <div
            className={`mt-2 flex items-center rounded-lg ${
              isCollapsed ? 'flex-col gap-2 py-1' : 'gap-2 p-1'
            }`}
          >
            <div
              title={isCollapsed ? 'My Account' : undefined}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-violet-600 text-xs font-semibold"
            >
              U
            </div>

            {!isCollapsed && (
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium text-zinc-200">
                  My Account
                </p>
                <p className="text-[10px] text-zinc-500">
                  Personal workspace
                </p>
              </div>
            )}

            {isCollapsed && (
              <button
                type="button"
                onClick={onToggleCollapse}
                aria-label="Expand sidebar"
                title="Expand sidebar"
                className="flex h-8 w-8 items-center justify-center rounded-lg text-zinc-400 transition hover:bg-white/[0.07] hover:text-white"
              >
                <PanelLeftOpen size={17} />
              </button>
            )}
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
