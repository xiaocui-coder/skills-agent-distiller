import { useState } from 'react'
import { Save, CheckCircle } from 'lucide-react'
import { Card } from '../../ui/Card'
import { Button } from '../../ui/Button'
import { MarkdownRenderer } from '../../common/MarkdownRenderer'
import { postSaveSkill } from '../../../api/rest'
import type { AutoGenResult as AutoGenResultType, ReferenceSection } from '../../../api/types'

function ActHeader({ act, title }: { act: number; title: string }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-xs font-medium text-zinc-500">ACT {act}</span>
      <span className="text-sm font-medium text-zinc-200">{title}</span>
    </div>
  )
}

function SaveButton({
  name, description, body,
  referenceTitle, referenceSections,
}: {
  name: string
  description: string
  body: string
  referenceTitle?: string
  referenceSections?: ReferenceSection[]
}) {
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      await postSaveSkill({
        name,
        description,
        body,
        reference_title: referenceTitle || '',
        reference_sections: referenceSections?.map((s) => ({ title: s.title, content: s.content })),
      })
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

export function AutoGenerateResult({ result }: { result: AutoGenResultType }) {
  const [visibleActs, setVisibleActs] = useState(1)
  const showNextAct = () => setVisibleActs((v) => Math.min(v + 1, 4))

  return (
    <div className="space-y-4">
      {/* Act 1: Intent */}
      {visibleActs >= 1 && (
        <Card>
          <ActHeader act={1} title="意图分析" />
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-zinc-500">领域:</span>
              <span className="text-zinc-300 ml-1">{result.intent.domain}</span>
            </div>
            <div>
              <span className="text-zinc-500">使用者:</span>
              <span className="text-zinc-300 ml-1">{result.intent.audience}</span>
            </div>
            <div className="col-span-2">
              <span className="text-zinc-500">核心任务:</span>
              <span className="text-zinc-300 ml-1">{result.intent.primary_task}</span>
            </div>
            {result.intent.triggers.length > 0 && (
              <div className="col-span-2">
                <span className="text-zinc-500">触发条件:</span>
                <ul className="mt-1 space-y-0.5">
                  {result.intent.triggers.map((t, i) => (
                    <li key={i} className="text-zinc-400">- {t}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {visibleActs < 4 && (
            <button onClick={showNextAct} className="mt-3 text-xs text-blue-400 hover:text-blue-300">继续展开 ▼</button>
          )}
        </Card>
      )}

      {/* Act 2: Outline */}
      {visibleActs >= 2 && (
        <Card>
          <ActHeader act={2} title="大纲规划" />
          {result.outline.rules.length > 0 && (
            <div className="mb-3">
              <span className="text-xs font-medium text-zinc-500">规则</span>
              <ol className="mt-1 space-y-1 list-decimal list-inside">
                {result.outline.rules.map((r, i) => (
                  <li key={i} className="text-xs text-zinc-300">{r}</li>
                ))}
              </ol>
            </div>
          )}
          {result.outline.examples.length > 0 && (
            <div className="mb-3">
              <span className="text-xs font-medium text-zinc-500">对照示例</span>
              <div className="mt-1 space-y-2">
                {result.outline.examples.map((ex, i) => (
                  <div key={i} className="rounded border border-zinc-800 p-2">
                    <p className="text-xs text-rose-400">反例: {ex.bad}</p>
                    <p className="text-xs text-emerald-400 mt-1">正例: {ex.good}</p>
                    {ex.reason && <p className="text-xs text-zinc-500 mt-1">原因: {ex.reason}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
          {visibleActs < 4 && (
            <button onClick={showNextAct} className="mt-3 text-xs text-blue-400 hover:text-blue-300">继续展开 ▼</button>
          )}
        </Card>
      )}

      {/* Act 3: Skill */}
      {visibleActs >= 3 && (
        <Card>
          <div className="flex items-center justify-between mb-3">
            <ActHeader act={3} title="Skill 生成" />
            <SaveButton
              name={result.skill.name}
              description={result.skill.description}
              body={result.skill.body}
              referenceTitle={result.reference.title}
              referenceSections={result.reference.sections}
            />
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
          {visibleActs < 4 && (
            <button onClick={showNextAct} className="mt-3 text-xs text-blue-400 hover:text-blue-300">继续展开 ▼</button>
          )}
        </Card>
      )}

      {/* Act 4: Reference */}
      {visibleActs >= 4 && (
        <Card>
          <ActHeader act={4} title="参考文档" />
          <h4 className="text-sm font-medium text-zinc-200 mb-2">{result.reference.title}</h4>
          <div className="space-y-3">
            {result.reference.sections.map((sec, i) => (
              <div key={i} className="rounded border border-zinc-800 p-3">
                <h5 className="text-xs font-medium text-zinc-300">{sec.title}</h5>
                <MarkdownRenderer content={sec.content} />
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
