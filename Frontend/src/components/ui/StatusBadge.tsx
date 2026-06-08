export function StatusBadge({ level }: { level: 'ok' | 'warn' | 'error' }) {
  const colors = {
    ok: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    warn: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    error: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  }
  const labels = { ok: 'OK', warn: 'WARN', error: 'ERROR' }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colors[level]}`}>
      {labels[level]}
    </span>
  )
}
