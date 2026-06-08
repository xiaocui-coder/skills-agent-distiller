import type { ReactNode } from 'react'

export function EmptyState({ icon, title, description }: { icon?: ReactNode; title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {icon && <div className="text-zinc-600 mb-4">{icon}</div>}
      <p className="text-zinc-400 text-sm">{title}</p>
      {description && <p className="text-zinc-600 text-xs mt-1">{description}</p>}
    </div>
  )
}
