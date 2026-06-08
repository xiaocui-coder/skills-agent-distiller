import { useState } from 'react'
import { useStoreSkills, useStoreSkill, useDeleteStoreSkill } from '../../../hooks/useDistiller'
import { Card } from '../../ui/Card'
import { Button } from '../../ui/Button'
import { Modal } from '../../ui/Modal'
import { EmptyState } from '../../ui/EmptyState'
import { LoadingSpinner } from '../../ui/LoadingSpinner'
import { Archive } from 'lucide-react'
import type { StoredSkillSummary, SkillVersion } from '../../../api/types'

export function StoreView() {
  const { data: skills, isLoading } = useStoreSkills()
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const { data: detail, isLoading: detailLoading } = useStoreSkill(selectedId || '')
  const deleteMutation = useDeleteStoreSkill()

  const handleDelete = () => {
    if (!deleteId) return
    deleteMutation.mutate(deleteId, {
      onSuccess: () => {
        setDeleteId(null)
        if (selectedId === deleteId) setSelectedId(null)
      },
    })
  }

  if (isLoading) return <LoadingSpinner className="py-16" />

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-zinc-300">已存储的 Skills</h3>

      {!skills || skills.length === 0 ? (
        <EmptyState icon={<Archive size={32} />} title="存储库为空" description="通过蒸馏或自动生成来创建 Skills" />
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {/* 列表 */}
          <div className="space-y-2">
            {(skills as StoredSkillSummary[]).map((s) => (
              <Card
                key={s.id}
                className={`cursor-pointer transition-colors ${selectedId === s.id ? 'border-blue-500/50 bg-blue-500/5' : 'hover:border-zinc-600'}`}
                onClick={() => setSelectedId(s.id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-zinc-200">{s.name}</p>
                    {s.scenario && <p className="text-xs text-zinc-500 mt-0.5">{s.scenario}</p>}
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-zinc-500">v{s.latest_version}</span>
                    <span className="text-xs text-zinc-600 ml-2">{s.versions_count} 版</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* 详情 */}
          <div>
            {selectedId && detailLoading && <LoadingSpinner />}
            {selectedId && detail && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-zinc-200">{detail.name}</h4>
                    <p className="text-xs text-zinc-500">{detail.source} · {detail.created_at}</p>
                  </div>
                  <Button size="sm" variant="danger" onClick={() => setDeleteId(detail.id)}>删除</Button>
                </div>
                {detail.versions.map((v) => (
                  <VersionCard key={v.v} version={v} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <Modal open={!!deleteId} onClose={() => setDeleteId(null)} title="确认删除">
        <p className="text-sm text-zinc-400 mb-4">确定要删除这个 Skill 吗？此操作不可撤销。</p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={() => setDeleteId(null)}>取消</Button>
          <Button variant="danger" size="sm" onClick={handleDelete} disabled={deleteMutation.isPending}>
            {deleteMutation.isPending ? '删除中...' : '删除'}
          </Button>
        </div>
      </Modal>
    </div>
  )
}

function VersionCard({ version }: { version: SkillVersion }) {
  const [open, setOpen] = useState(false)
  return (
    <Card className="cursor-pointer" onClick={() => setOpen(!open)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-zinc-400">v{version.v}</span>
          <span className="text-xs text-zinc-300">{version.description}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-600">{version.signal_count} 信号</span>
          <span className="text-xs text-zinc-600">{open ? '▼' : '▶'}</span>
        </div>
      </div>
      {open && (
        <div className="mt-2 pt-2 border-t border-zinc-800 space-y-2">
          {version.body && (
            <pre className="text-xs text-zinc-400 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto bg-zinc-800 rounded p-2">
              {version.body}
            </pre>
          )}
          {version.added_conversation && (
            <div>
              <span className="text-xs text-zinc-500">新增对话:</span>
              <pre className="text-xs text-zinc-500 font-mono whitespace-pre-wrap max-h-20 overflow-y-auto mt-1">
                {version.added_conversation.slice(0, 500)}
              </pre>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
