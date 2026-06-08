import { useState } from 'react'
import { postLint } from '../../../api/rest'
import { Button } from '../../ui/Button'
import { Card } from '../../ui/Card'
import { StatusBadge } from '../../ui/StatusBadge'
import type { LintResult } from '../../../api/types'

export function LintView() {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [body, setBody] = useState('')
  const [result, setResult] = useState<LintResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleLint = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await postLint({ name, description, body })
      setResult(res)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-zinc-500 mb-1">Skill 名称</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="my-skill"
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-500 font-mono"
          />
        </div>
        <div>
          <label className="block text-xs text-zinc-500 mb-1">描述</label>
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Skill 的用途和触发条件"
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-500"
          />
        </div>
      </div>
      <div>
        <label className="block text-xs text-zinc-500 mb-1">SKILL.md 正文</label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="## 必须避免&#10;- 不要使用 var&#10;..."
          rows={6}
          className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-600 font-mono focus:outline-none focus:border-zinc-500 resize-y"
        />
      </div>
      <Button onClick={handleLint} disabled={loading}>
        {loading ? '校验中...' : '开始校验'}
      </Button>

      {error && <Card className="border-rose-500/30 bg-rose-500/10"><p className="text-sm text-rose-400">{error}</p></Card>}

      {result && (
        <Card>
          {/* Summary */}
          <div className="flex items-center gap-4 mb-4">
            {Object.entries(result.summary).map(([field, level]) => (
              <div key={field} className="flex items-center gap-2">
                <span className="text-xs text-zinc-500">{field}:</span>
                <StatusBadge level={level as 'ok' | 'warn' | 'error'} />
              </div>
            ))}
          </div>
          {/* Items */}
          {result.items.length > 0 && (
            <div className="border-t border-zinc-800 pt-3">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-zinc-500 text-left">
                    <th className="pb-2 pr-3">字段</th>
                    <th className="pb-2 pr-3">级别</th>
                    <th className="pb-2 pr-3">消息</th>
                    <th className="pb-2">规则</th>
                  </tr>
                </thead>
                <tbody>
                  {result.items.map((item, i) => (
                    <tr key={i} className="border-t border-zinc-800/50">
                      <td className="py-2 pr-3 text-zinc-400">{item.field}</td>
                      <td className="py-2 pr-3"><StatusBadge level={item.level} /></td>
                      <td className="py-2 pr-3 text-zinc-300">{item.message}</td>
                      <td className="py-2 text-zinc-500 font-mono">{item.rule}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
