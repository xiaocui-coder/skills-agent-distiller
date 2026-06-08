import { useWebSocket } from '../../hooks/useWebSocket'
import { useChatStore } from '../../stores/chatStore'
import { ChatInput } from './ChatInput'
import { MessageList } from './MessageList'

export function ChatView() {
  const status = useChatStore((s) => s.status)
  const { send, reconnect } = useWebSocket('ws://localhost:8000/ws/chat')

  return (
    <div className="flex flex-col h-full">
      {status === 'disconnected' && (
        <div className="flex items-center justify-center gap-3 py-3 bg-zinc-900/50 border-b border-zinc-800">
          <span className="text-xs text-zinc-500">WebSocket 未连接</span>
          <button onClick={reconnect} className="text-xs text-blue-400 hover:text-blue-300">重新连接</button>
        </div>
      )}
      <MessageList />
      <ChatInput onSend={send} disabled={status !== 'connected'} />
    </div>
  )
}
