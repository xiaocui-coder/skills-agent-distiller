import { NavLink } from 'react-router-dom'
import { MessageSquare, Package, FlaskConical, PanelLeftClose, PanelLeft } from 'lucide-react'
import { useAppStore } from '../../stores/appStore'
import { useHealth } from '../../hooks/useHealth'

const navItems = [
  { to: '/chat', icon: MessageSquare, label: '对话' },
  { to: '/skills', icon: Package, label: '技能库' },
  { to: '/distiller', icon: FlaskConical, label: '蒸馏器' },
]

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useAppStore()
  const { data: health } = useHealth()

  return (
    <aside className={`flex flex-col border-r border-zinc-800 bg-zinc-950 transition-all duration-200 ${sidebarOpen ? 'w-56' : 'w-14'}`}>
      <div className="flex items-center justify-between p-3 border-b border-zinc-800">
        {sidebarOpen && <span className="text-sm font-semibold text-zinc-200">Skills Agent</span>}
        <button onClick={toggleSidebar} className="p-1.5 rounded hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors">
          {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeft size={18} />}
        </button>
      </div>

      <nav className="flex-1 p-2 space-y-1 mt-2">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive
                  ? 'bg-zinc-800 text-zinc-100'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
              }`
            }
          >
            <Icon size={18} />
            {sidebarOpen && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-zinc-800">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            health?.agent_ready ? 'bg-emerald-400' :
            health?.status === 'ok' ? 'bg-amber-400' : 'bg-zinc-600'
          }`} />
          {sidebarOpen && (
            <span className="text-xs text-zinc-500">
              {health?.agent_ready ? 'Agent 就绪' : health?.status === 'ok' ? '部分就绪' : '未连接'}
            </span>
          )}
        </div>
        {sidebarOpen && health?.distiller_ready === false && (
          <span className="text-xs text-zinc-600 mt-1 block">蒸馏器未就绪</span>
        )}
      </div>
    </aside>
  )
}
