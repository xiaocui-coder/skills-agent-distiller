import { useState } from 'react'
import { Save, CheckCircle } from 'lucide-react'
import { Card } from '../../ui/Card'
import { Button } from '../../ui/Button'
import { MarkdownRenderer } from '../../common/MarkdownRenderer'
import { postSaveSkill } from '../../../api/rest'
import type { DistillResult as DistillResultType } from '../../../api/types'

const signalLabels: Record<string, { label: string; emoji: string; color: string }> = {
  preference: { label: '偏好', emoji: '💛', color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
  constraint: { label: '约束', emoji: '🚫', color: 'text-rose-400 bg-rose-500/10 border-rose-500/30' },
  workflow:   { label: '工作流', emoji: '🔄', color: 'text-sky-400 bg-sky-500/10 border-sky-500/30' },
  example:    { label: '示例', emoji: '📌', color: 'text-violet-400 bg-violet-500/10 border-violet-500/30' },
}

function ActHeader({ act, title }: { act: number; title: string }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-xs font-medium text-zinc-500">ACT {act}</span>
      <span className="text-sm font-medium text-zinc-200">{title}</span>
    </div>
  )
}

function SaveButton({ name, description, body }: { name: string; description: string; body: string }) {
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      await postSaveSkill({ name, description, body })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <Button
        size="sm"
        variant={saved ? 'secondary' : 'primary'}
        onClick={handleSave}
        disabled={saving || saved}
      >
        {saved ? <CheckCircle size={14} /> : <Save size={14} />}
        {saved ? '已保存' : saving ? '保存中...' : '保存到技能库'}
      </Button>
      {error && <p className="text-xs text-rose-400 mt-1">{error}</p>}
    </div>
  )
}

export function DistillResult({ result }: { result: DistillResultType }) {
  const [visibleActs, setVisibleActs] = useState(1)

  const showNextAct = () => setVisibleActs((v) => Math.min(v + 1, 3))

  return (
    <div className="space-y-4">
      {/* Act 1: Signals */}
      {visibleActs >= 1 && (
        <Card className="animate-in fade-in slide-in-from-bottom-2">
          <ActHeader act={1} title="信号提取" />
          {result.signals.length === 0 ? (
            <p className="text-xs text-zinc-500">未提取到信号</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {result.signals.map((sig, i) => {
                const meta = signalLabels[sig.type] || signalLabels.preference
                return (
                  <span
                    key={i}
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs ${meta.color}`}
                  >
                    <span>{meta.emoji}</span>
                    <span>{sig.text}</span>
                  </span>
                )
              })}
            </div>
          )}
          {visibleActs < 3 && (
            <button onClick={showNextAct} className="mt-3 text-xs text-blue-400 hover:text-blue-300">
              继续展开 ▼
            </button>
          )}
        </Card>
      )}

      {/* Act 2: Clusters */}
      {visibleActs >= 2 && (
        <Card className="animate-in fade-in slide-in-from-bottom-2">
          <ActHeader act={2} title="分类归纳" />
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: '偏好', items: result.clusters.preferences, emoji: '💛', color: 'border-amber-500/20' },
              { label: '约束', items: result.clusters.constraints, emoji: '🚫', color: 'border-rose-500/20' },
              { label: '工作流', items: result.clusters.workflows, emoji: '🔄', color: 'border-sky-500/20' },
              { label: '示例', items: result.clusters.examples, emoji: '📌', color: 'border-violet-500/20' },
            ].map((group) => (
              <div key={group.label} className={`rounded-md border p-3 ${group.color}`}>
                <div className="text-xs font-medium text-zinc-400 mb-1.5">{group.emoji} {group.label}</div>
                <ul className="space-y-1">
                  {group.items.map((item, i) => (
                    <li key={i} className="text-xs text-zinc-300">{item}</li>
                  ))}
                  {group.items.length === 0 && <li className="text-xs text-zinc-600">无</li>}
                </ul>
              </div>
            ))}
          </div>
          {visibleActs < 3 && (
            <button onClick={showNextAct} className="mt-3 text-xs text-blue-400 hover:text-blue-300">
              继续展开 ▼
            </button>
          )}
        </Card>
      )}

      {/* Act 3: Skill */}
      {visibleActs >= 3 && (
        <Card className="animate-in fade-in slide-in-from-bottom-2">
          <div className="flex items-center justify-between mb-3">
            <ActHeader act={3} title="Skill 生成" />
            <SaveButton name={result.skill.name} description={result.skill.description} body={result.skill.body} />
          </div>
          <div className="space-y-2">
            <div>
              <span className="text-xs text-zinc-500">name:</span>
              <span className="text-sm text-zinc-200 ml-2 font-mono">{result.skill.name}</span>
            </div>
            {result.skill.description && (
              <div>
                <span className="text-xs text-zinc-500">description:</span>
                <span className="text-sm text-zinc-300 ml-2">{result.skill.description}</span>
              </div>
            )}
            {result.skill.body && (
              <div className="border-t border-zinc-800 pt-3 mt-3">
                <MarkdownRenderer content={result.skill.body} />
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}
