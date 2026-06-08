import { MarkdownRenderer } from '../common/MarkdownRenderer'
import { ThinkingBlock } from './ThinkingBlock'
import { ToolCallBlock } from './ToolCallBlock'
import type { ChatMessage } from '../../stores/chatStore'

interface Props {
  message: ChatMessage
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  return (
    <div className="flex gap-3">
      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs flex-shrink-0 mt-0.5 ${
        isUser
          ? 'bg-blue-600/20 text-blue-400'
          : 'bg-violet-600/20 text-violet-400'
      }`}>
        {isUser ? 'U' : 'AI'}
      </div>
      <div className="flex-1 min-w-0 space-y-2">
        {message.thinking.map((t) => (
          <ThinkingBlock key={t.id} content={t.content} />
        ))}
        {message.toolCalls.map((tc) => (
          <ToolCallBlock key={tc.id} name={tc.name} args={tc.args} result={tc.result} success={tc.success} />
        ))}
        {message.content && (
          <MarkdownRenderer content={message.content} />
        )}
      </div>
    </div>
  )
}
