import { useState } from 'react'
import { useAutoGenerateStream } from '../../../hooks/useAutoGenerateStream'
import { useAutoClarify } from '../../../hooks/useDistiller'
import { Button } from '../../ui/Button'
import { Card } from '../../ui/Card'
import { ClarifyQuestions } from './ClarifyQuestions'
import { AutoGenerateResult } from './AutoGenerateResult'
import type { ClarifyResult } from '../../../api/types'

export function AutoGenerateView() {
  const [input, setInput] = useState('')
  const [clarifyResult, setClarifyResult] = useState<ClarifyResult | null>(null)
  const [answers, setAnswers] = useState<string[]>([])
  const { streaming, rawText, result, error, start, reset } = useAutoGenerateStream()
  const clarify = useAutoClarify()

  const handleClarify = async () => {
    if (!input.trim()) return
    try {
      const res = await clarify.mutateAsync(input)
      setClarifyResult(res)
      setAnswers(res.questions.map((q) => q.recommended_answer || ''))
    } catch {
      // error handled by mutation
    }
  }

  const handleGenerate = () => {
    start(input, answers.length > 0 ? answers : undefined)
  }

  const handleReset = () => {
    reset()
    setClarifyResult(null)
    setAnswers([])
  }

  return (
    <div className="space-y-4">
      {/* 需求描述 */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-2">需求描述</label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="描述你想要的 Skill，例如：帮我做一个前端代码审查 Skill"
          rows={4}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-500 resize-y"
        />
        <div className="flex gap-2 mt-3">
          <Button onClick={handleClarify} disabled={!input.trim() || clarify.isPending}>
            {clarify.isPending ? '生成中...' : '生成澄清问题'}
          </Button>
          <Button variant="secondary" onClick={handleGenerate} disabled={!input.trim() || streaming}>
            跳过澄清，直接生成
          </Button>
          {(clarifyResult || result) && <Button variant="ghost" onClick={handleReset}>重置</Button>}
        </div>
        {clarify.isError && (
          <p className="text-xs text-rose-400 mt-2">生成澄清问题失败</p>
        )}
      </div>

      {/* 澄清问题 */}
      {clarifyResult && (
        <Card>
          <h3 className="text-sm font-medium text-zinc-300 mb-3">澄清问题</h3>
          <ClarifyQuestions questions={clarifyResult.questions} answers={answers} onChange={setAnswers} />
          <div className="mt-3">
            <Button onClick={handleGenerate} disabled={streaming}>
              {streaming ? '生成中...' : '开始生成'}
            </Button>
          </div>
        </Card>
      )}

      {/* 错误 */}
      {error && (
        <Card className="border-rose-500/30 bg-rose-500/10">
          <p className="text-sm text-rose-400">{error}</p>
        </Card>
      )}

      {/* 流式输出 */}
      {streaming && rawText && (
        <Card>
          <h3 className="text-xs font-medium text-zinc-500 mb-2">生成中...</h3>
          <pre className="text-xs text-zinc-400 whitespace-pre-wrap font-mono max-h-60 overflow-y-auto">{rawText}</pre>
        </Card>
      )}

      {/* 4幕结果 */}
      {result && <AutoGenerateResult result={result} />}
    </div>
  )
}
