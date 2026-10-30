import {
  BrainCircuit,
  LayoutDashboard,
  Files,
  MessageSquare,
  SlidersHorizontal,
  Settings2,
  PanelLeftClose,
  PanelLeftOpen,
  X,
  FileText,
  Code,
  LogOut,
} from 'lucide-react'

import { logout } from '../../services/api'

const navigationItems = [
  { label: 'Overview', icon: LayoutDashboard },
  { label: 'Knowledge Sources', icon: Files },
  { label: 'Uploaded Documents', icon: FileText },
  { label: 'Test Assistant', icon: MessageSquare },
  { label: 'Assistant Setup', icon: SlidersHorizontal },
  { label: 'Install', icon: Code },
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

  // Collapsed only applies on lg+. The mobile drawer is always full width with labels.
  const hideWhenCollapsed = isCollapsed ? 'lg:hidden' : ''

  const navButtonClass = (active) =>
    `flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2.5 text-[13px] outline-none transition focus-visible:ring-2 focus-visible:ring-violet-500/60 ${
      isCollapsed ? 'lg:justify-center lg:gap-0 lg:px-1' : ''
    } ${
      active
        ? 'bg-violet-500/10 font-medium text-violet-200'
        : 'text-zinc-400 hover:bg-white/[0.04] hover:text-zinc-100'
    }`

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
        className={`fixed inset-y-0 left-0 z-50 flex h-dvh w-[260px] shrink-0 flex-col border-r border-white/[0.08] bg-[#111114] text-white transition-[width,transform] duration-200 lg:sticky lg:top-0 lg:z-20 ${
          isCollapsed ? 'lg:w-[68px]' : 'lg:w-[260px]'
        } ${
          isOpen
            ? 'translate-x-0'
            : '-translate-x-full invisible lg:translate-x-0 lg:visible'
        }`}
      >
        {/* Header */}
        <div
          className={`flex h-14 shrink-0 items-center justify-between border-b border-white/[0.07] px-3 ${
            isCollapsed ? 'lg:justify-center lg:px-1' : ''
          }`}
        >
          <div className="flex min-w-0 items-center gap-2.5">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-600">
              <BrainCircuit size={21} />
            </div>

            <div className={`min-w-0 ${hideWhenCollapsed}`}>
              <p className="text-base font-semibold tracking-tight">knowvia</p>
              <p className="text-[11px] text-zinc-500">Business AI</p>
            </div>
          </div>

          {!isCollapsed && (
            <button
              type="button"
              onClick={onToggleCollapse}
              aria-label="Collapse sidebar"
              title="Collapse sidebar"
              className="hidden h-8 w-8 shrink-0 items-center justify-center rounded-lg text-zinc-500 outline-none transition hover:bg-white/[0.06] hover:text-white focus-visible:ring-2 focus-visible:ring-violet-500/60 lg:flex"
            >
              <PanelLeftClose size={17} />
            </button>
          )}

          <button
            type="button"
            onClick={onClose}
            aria-label="Close sidebar"
            className="rounded-lg p-2 text-zinc-400 outline-none hover:bg-white/5 focus-visible:ring-2 focus-visible:ring-violet-500/60 lg:hidden"
          >
            <X size={19} />
          </button>
        </div>

        {/* Workspace tile (static until multi-tenant is decided) */}
        <div className="shrink-0 p-2.5">
          <div
            title={isCollapsed ? 'My Workspace' : undefined}
            className={`flex w-full items-center gap-2.5 rounded-lg border border-white/[0.07] bg-white/[0.02] p-2 ${
              isCollapsed ? 'lg:justify-center lg:gap-0' : ''
            }`}
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-violet-500/15 text-sm font-medium text-violet-200">
              W
            </div>

            <div className={`min-w-0 flex-1 text-left ${hideWhenCollapsed}`}>
              <p className="truncate text-xs font-medium">My Workspace</p>
              <p className="mt-0.5 text-[11px] text-zinc-500">Free plan</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto px-2.5">
          <p
            className={`mb-2 px-2 text-[10px] font-medium tracking-widest text-zinc-600 ${hideWhenCollapsed}`}
          >
            WORKSPACE
          </p>

          {navigationItems.map(({ label, icon: Icon }) => {
            const isActive = activePage === label

            return (
              <button
                key={label}
                type="button"
                title={isCollapsed ? label : undefined}
                aria-current={isActive ? 'page' : undefined}
                onClick={() => handleNavigate(label)}
                className={navButtonClass(isActive)}
              >
                <Icon size={17} className="shrink-0" />
                <span className={`truncate ${hideWhenCollapsed}`}>{label}</span>
              </button>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="mt-auto shrink-0 border-t border-white/[0.07] p-2.5">
          <button
            type="button"
            title={isCollapsed ? 'Settings' : undefined}
            aria-current={activePage === 'Settings' ? 'page' : undefined}
            onClick={() => handleNavigate('Settings')}
            className={navButtonClass(activePage === 'Settings')}
          >
            <Settings2 size={17} className="shrink-0" />
            <span className={hideWhenCollapsed}>Settings</span>
          </button>

          <div
            className={`mt-2 flex items-center gap-2 rounded-lg p-1 ${
              isCollapsed ? 'lg:flex-col lg:gap-2 lg:px-0' : ''
            }`}
          >
            <div
              title={isCollapsed ? 'My Account' : undefined}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-violet-600 text-xs font-semibold"
            >
              U
            </div>

            <div className={`min-w-0 flex-1 ${hideWhenCollapsed}`}>
              <p className="truncate text-xs font-medium text-zinc-200">
                My Account
              </p>
              <p className="text-[10px] text-zinc-500">Personal workspace</p>
            </div>

            {!isCollapsed && (
              <button
                type="button"
                onClick={logout}
                aria-label="Log out"
                title="Log out"
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-zinc-500 outline-none transition hover:bg-white/[0.07] hover:text-white focus-visible:ring-2 focus-visible:ring-violet-500/60"
              >
                <LogOut size={17} />
              </button>
            )}

            {isCollapsed && (
              <button
                type="button"
                onClick={onToggleCollapse}
                aria-label="Expand sidebar"
                title="Expand sidebar"
                className="hidden h-8 w-8 items-center justify-center rounded-lg text-zinc-400 outline-none transition hover:bg-white/[0.07] hover:text-white focus-visible:ring-2 focus-visible:ring-violet-500/60 lg:flex"
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