import { useState } from 'react'
import { Brain } from 'lucide-react'

export function ThinkingBlock({ content }: { content: string }) {
  const [open, setOpen] = useState(false)
  if (!content) return null

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 w-full text-left text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
      >
        <Brain size={12} />
        <span>思考过程</span>
        <span className="text-zinc-600">{open ? '▼' : '▶'}</span>
      </button>
      {open && (
        <div className="px-3 pb-3 text-xs text-zinc-500 whitespace-pre-wrap border-t border-zinc-800 pt-2 max-h-60 overflow-y-auto">
          {content}
        </div>
      )}
    </div>
  )
}
