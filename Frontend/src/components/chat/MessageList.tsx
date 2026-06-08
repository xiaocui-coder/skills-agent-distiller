import { useEffect, useRef } from 'react'
import { useChatStore } from '../../stores/chatStore'
import { MessageBubble } from './MessageBubble'
import { ThinkingBlock } from './ThinkingBlock'
import { ToolCallBlock } from './ToolCallBlock'

export function MessageList() {
  const messages = useChatStore((s) => s.messages)
  const currentStreaming = useChatStore((s) => s.currentStreaming)
  const currentThinking = useChatStore((s) => s.currentThinking)
  const currentToolCalls = useChatStore((s) => s.currentToolCalls)
  const isStreaming = useChatStore((s) => s.isStreaming)
  const error = useChatStore((s) => s.error)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, currentStreaming, currentThinking.length, currentToolCalls.length, error])

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center py-20">
            <p className="text-zinc-500 text-sm">开始与 Agent 对话</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isStreaming && (
          <div className="space-y-3">
            {currentThinking.map((t) => (
              <ThinkingBlock key={t.id} content={t.content} />
            ))}
            {currentToolCalls.map((tc) => (
              <ToolCallBlock key={tc.id} name={tc.name} args={tc.args} result={tc.result} success={tc.success} />
            ))}
            {currentStreaming && (
              <div className="flex gap-3">
                <div className="w-7 h-7 rounded-full bg-violet-600/20 flex items-center justify-center text-xs text-violet-400 flex-shrink-0 mt-0.5">AI</div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-zinc-200 whitespace-pre-wrap">
                    {currentStreaming}
                    <span className="inline-block w-1.5 h-4 bg-zinc-400 animate-pulse ml-0.5 align-middle" />
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        {error && (
          <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-400">
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
