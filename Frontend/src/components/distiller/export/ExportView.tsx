import { useState } from 'react'
import { useSkills } from '../../../hooks/useSkills'
import { useExportTargets } from '../../../hooks/useDistiller'
import { useExportDownload } from '../../../hooks/useExportDownload'
import { postExport } from '../../../api/rest'
import { Button } from '../../ui/Button'
import { Card } from '../../ui/Card'
import { LoadingSpinner } from '../../ui/LoadingSpinner'

export function ExportView() {
  const { data: skills } = useSkills()
  const { data: targets } = useExportTargets()
  const { download } = useExportDownload()
  const [skillName, setSkillName] = useState('')
  const [selectedTarget, setSelectedTarget] = useState('')
  const [preview, setPreview] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handlePreview = async () => {
    if (!skillName || !selectedTarget) return
    setLoading(true)
    try {
      const res = await postExport({ skill_name: skillName, target: selectedTarget })
      setPreview(res.content)
    } catch {
      setPreview(null)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!skillName || !selectedTarget) return
    await download(skillName, selectedTarget)
  }

  const skillNames = skills?.map((s) => s.name) || []

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-zinc-500 mb-1">选择 Skill</label>
          <select
            value={skillName}
            onChange={(e) => setSkillName(e.target.value)}
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-zinc-500"
          >
            <option value="">-- 选择 --</option>
            {skillNames.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-zinc-500 mb-1">导出格式</label>
          <div className="flex gap-2 flex-wrap">
            {targets?.map((t) => (
              <button
                key={t.key}
                onClick={() => setSelectedTarget(t.key)}
                className={`px-3 py-1.5 rounded-md border text-xs transition-colors ${
                  selectedTarget === t.key
                    ? 'border-blue-500/50 bg-blue-500/10 text-blue-300'
                    : 'border-zinc-700 bg-zinc-900 text-zinc-400 hover:border-zinc-600'
                }`}
              >
                <span className="mr-1">{t.emoji}</span> {t.title}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex gap-2">
        <Button onClick={handlePreview} disabled={!skillName || !selectedTarget || loading}>
          {loading ? '加载中...' : '预览'}
        </Button>
        <Button variant="secondary" onClick={handleDownload} disabled={!skillName || !selectedTarget}>
          下载
        </Button>
      </div>

      {preview && (
        <Card>
          <h3 className="text-xs font-medium text-zinc-500 mb-2">预览</h3>
          <pre className="text-xs text-zinc-300 font-mono whitespace-pre-wrap max-h-96 overflow-y-auto bg-zinc-800 rounded p-3">
            {preview}
          </pre>
          {targets?.find((t) => t.key === selectedTarget)?.hint && (
            <p className="text-xs text-zinc-500 mt-2">
              {targets.find((t) => t.key === selectedTarget)?.hint}
            </p>
          )}
        </Card>
      )}
    </div>
  )
}
