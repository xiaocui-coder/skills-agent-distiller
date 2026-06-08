import { Link } from 'react-router-dom'
import { Package } from 'lucide-react'
import { Card } from '../ui/Card'
import { EmptyState } from '../ui/EmptyState'
import type { SkillSummary } from '../../api/types'

export function SkillsList({ skills }: { skills: SkillSummary[] }) {
  if (skills.length === 0) {
    return <EmptyState icon={<Package size={32} />} title="暂无 Skills" description="运行 distill 或 auto-generate 来创建 Skills" />
  }

  return (
    <div className="grid gap-3">
      {skills.map((skill) => (
        <Link key={skill.name} to={`/skills/${encodeURIComponent(skill.name)}`}>
          <Card className="hover:border-zinc-600 transition-colors cursor-pointer">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded bg-blue-500/10 flex items-center justify-center flex-shrink-0">
                <Package size={14} className="text-blue-400" />
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-medium text-zinc-100">{skill.name}</h3>
                <p className="text-xs text-zinc-500 mt-1 line-clamp-2">{skill.description || '无描述'}</p>
              </div>
            </div>
          </Card>
        </Link>
      ))}
    </div>
  )
}
