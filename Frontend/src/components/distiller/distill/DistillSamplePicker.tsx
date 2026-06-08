import type { SampleSummary } from '../../../api/types'

export function DistillSamplePicker({ samples, selected, onSelect }: {
  samples: SampleSummary[]
  selected: string | null
  onSelect: (key: string) => void
}) {
  return (
    <div className="flex gap-2 flex-wrap">
      {samples.map((s) => (
        <button
          key={s.key}
          onClick={() => onSelect(s.key === selected ? '' : s.key)}
          className={`px-3 py-2 rounded-lg border text-left transition-colors ${
            selected === s.key
              ? 'border-blue-500/50 bg-blue-500/10'
              : 'border-zinc-700 bg-zinc-900 hover:border-zinc-600'
          }`}
        >
          <span className="text-sm mr-1">{s.emoji}</span>
          <span className="text-xs text-zinc-300">{s.title}</span>
        </button>
      ))}
    </div>
  )
}
