import type { ClarifyQuestion } from '../../../api/types'

export function ClarifyQuestions({ questions, answers, onChange }: {
  questions: ClarifyQuestion[]
  answers: string[]
  onChange: (answers: string[]) => void
}) {
  return (
    <div className="space-y-3">
      {questions.map((q, i) => (
        <div key={i} className="rounded-md border border-zinc-800 p-3">
          <p className="text-sm text-zinc-200 mb-2">
            <span className="text-zinc-500 mr-1">{i + 1}.</span>
            {q.q}
          </p>
          <textarea
            value={answers[i] || ''}
            onChange={(e) => {
              const next = [...answers]
              next[i] = e.target.value
              onChange(next)
            }}
            placeholder="输入你的回答..."
            rows={2}
            className="w-full rounded border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-500 resize-y"
          />
        </div>
      ))}
    </div>
  )
}
