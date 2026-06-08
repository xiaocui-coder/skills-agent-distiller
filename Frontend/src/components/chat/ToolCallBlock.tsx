import { useState } from 'react'
import { Wrench, CheckCircle, XCircle } from 'lucide-react'

interface Props {
  name: string
  args: Record<string, unknown>
  result?: string
  success?: boolean
}

export function ToolCallBlock({ name, args, result, success }: Props) {
  const [open, setOpen] = useState(false)

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 w-full text-left text-xs transition-colors"
      >
        <Wrench size={12} className="text-zinc-500" />
        <span className="text-zinc-300">{name}</span>
        <span className="text-zinc-600">{open ? '▼' : '▶'}</span>
        {result !== undefined && (
          success ? <CheckCircle size={12} className="text-emerald-400 ml-auto" /> : <XCircle size={12} className="text-rose-400 ml-auto" />
        )}
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-2 border-t border-zinc-800 pt-2">
          <div className="text-xs">
            <span className="text-zinc-500">参数:</span>
            <pre className="mt-1 p-2 bg-zinc-800 rounded text-zinc-300 overflow-x-auto max-h-32 overflow-y-auto">
              {JSON.stringify(args, null, 2)}
            </pre>
          </div>
          {result !== undefined && (
            <div className="text-xs">
              <span className="text-zinc-500">结果:</span>
              <pre className={`mt-1 p-2 rounded overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap ${
                success ? 'bg-emerald-500/10 text-emerald-300' : 'bg-rose-500/10 text-rose-300'
              }`}>
                {result.length > 1000 ? result.slice(0, 1000) + '\n... (truncated)' : result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
