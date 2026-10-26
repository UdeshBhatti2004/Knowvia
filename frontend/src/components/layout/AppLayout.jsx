
import { useState } from 'react'
import { Menu } from 'lucide-react'
import Sidebar from './Sidebar'

function AppLayout({ children, activePage, onNavigate }) {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  return (
    <div className="flex h-screen w-full overflow-hidden bg-[#0b0b0e] text-white">
      <Sidebar
        isOpen={isMobileSidebarOpen}
        onClose={() => setIsMobileSidebarOpen(false)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() =>
          setIsSidebarCollapsed((current) => !current)
        }
        activePage={activePage}
        onNavigate={onNavigate}
      />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex h-12 shrink-0 items-center gap-3 border-b border-white/[0.07] bg-[#0b0b0e] px-4 lg:hidden">
          <button
            type="button"
            onClick={() => setIsMobileSidebarOpen(true)}
            aria-label="Open navigation menu"
            aria-expanded={isMobileSidebarOpen}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-zinc-300 transition hover:bg-white/[0.06] hover:text-white"
          >
            <Menu size={19} />
          </button>

          <span className="text-sm font-semibold tracking-tight">
            knowvia
          </span>
        </header>

        <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  )
}

export default AppLayout
