import { useQuery } from '@tanstack/react-query'
import { getConfig } from '../../api/rest'
import { Wifi, WifiOff } from 'lucide-react'
import { useChatStore } from '../../stores/chatStore'

export function Header() {
  const { data: config } = useQuery({ queryKey: ['config'], queryFn: getConfig, staleTime: 60_000 })
  const status = useChatStore((s) => s.status)
  const reconnect = useChatStore.getState // we'll use the hook's reconnect in ChatPage

  return (
    <header className="h-12 flex items-center justify-between px-4 border-b border-zinc-800 bg-zinc-950">
      <div className="flex items-center gap-3 text-xs text-zinc-500">
        <span>模型: <span className="text-zinc-300">{config?.model || '...'}</span></span>
        {config?.distiller_enabled && <span className="text-violet-400/70">蒸馏器启用</span>}
      </div>
      <div className="flex items-center gap-2">
        <div className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs ${
          status === 'connected' ? 'text-emerald-400' :
          status === 'connecting' || status === 'reconnecting' ? 'text-amber-400' : 'text-zinc-500'
        }`}>
          {status === 'connected' ? <Wifi size={12} /> : <WifiOff size={12} />}
          <span>{status === 'connected' ? '已连接' : status === 'connecting' ? '连接中' : status === 'reconnecting' ? '重连中' : '未连接'}</span>
        </div>
      </div>
    </header>
  )
}
