import { useState } from 'react'
import { postDiff } from '../../../api/rest'
import { Button } from '../../ui/Button'
import { Card } from '../../ui/Card'
import type { DiffResult } from '../../../api/types'

export function DiffView() {
  const [oldBody, setOldBody] = useState('')
  const [newBody, setNewBody] = useState('')
  const [result, setResult] = useState<DiffResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDiff = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await postDiff({ old_body: oldBody, new_body: newBody })
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
          <label className="block text-xs text-zinc-500 mb-1">旧版本</label>
          <textarea
            value={oldBody}
            onChange={(e) => setOldBody(e.target.value)}
            placeholder="粘贴旧版 SKILL.md..."
            rows={6}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-600 font-mono focus:outline-none focus:border-zinc-500 resize-y"
          />
        </div>
        <div>
          <label className="block text-xs text-zinc-500 mb-1">新版本</label>
          <textarea
            value={newBody}
            onChange={(e) => setNewBody(e.target.value)}
            placeholder="粘贴新版 SKILL.md..."
            rows={6}
            className="w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder-zinc-600 font-mono focus:outline-none focus:border-zinc-500 resize-y"
          />
        </div>
      </div>
      <Button onClick={handleDiff} disabled={loading}>
        {loading ? '对比中...' : '开始对比'}
      </Button>

      {error && <Card className="border-rose-500/30 bg-rose-500/10"><p className="text-sm text-rose-400">{error}</p></Card>}

      {result && (
        <div className="space-y-3">
          {/* Stats */}
          <div className="flex items-center gap-4 text-xs">
            <span className="text-emerald-400">+{result.stats.added} 新增</span>
            <span className="text-rose-400">-{result.stats.removed} 移除</span>
            <span className="text-zinc-400">={result.stats.kept} 保留</span>
          </div>

          {/* Added */}
          {result.added.length > 0 && (
            <Card className="border-emerald-500/20">
              <h4 className="text-xs font-medium text-emerald-400 mb-2">新增规则</h4>
              {result.added.map((r, i) => (
                <div key={i} className="text-xs text-emerald-300/80 py-0.5">
                  <span className="text-zinc-500">[{r.section}]</span> {r.text}
                </div>
              ))}
            </Card>
          )}

          {/* Removed */}
          {result.removed.length > 0 && (
            <Card className="border-rose-500/20">
              <h4 className="text-xs font-medium text-rose-400 mb-2">移除规则</h4>
              {result.removed.map((r, i) => (
                <div key={i} className="text-xs text-rose-300/80 py-0.5">
                  <span className="text-zinc-500">[{r.section}]</span> {r.text}
                </div>
              ))}
            </Card>
          )}

          {/* Kept */}
          {result.kept.length > 0 && (
            <Card className="border-zinc-700">
              <h4 className="text-xs font-medium text-zinc-400 mb-2">保留规则</h4>
              {result.kept.map((r, i) => (
                <div key={i} className="text-xs text-zinc-500 py-0.5">
                  <span className="text-zinc-600">[{r.section}]</span> {r.text}
                </div>
              ))}
            </Card>
          )}

          {(result.added.length === 0 && result.removed.length === 0 && result.kept.length === 0) && (
            <p className="text-xs text-zinc-500">无差异</p>
          )}
        </div>
      )}
    </div>
  )
}
