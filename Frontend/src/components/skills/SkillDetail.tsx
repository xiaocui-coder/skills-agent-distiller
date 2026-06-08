import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'
import { MarkdownRenderer } from '../common/MarkdownRenderer'
import { Card } from '../ui/Card'
import { LoadingSpinner } from '../ui/LoadingSpinner'
import type { SkillDetail as SkillDetailType } from '../../api/types'

export function SkillDetail({ skill, loading, error }: { skill?: SkillDetailType; loading?: boolean; error?: Error | null }) {
  if (loading) return <LoadingSpinner className="py-16" />
  if (error) {
    return (
      <div className="text-center py-16">
        <p className="text-sm text-red-400">加载失败: {error.message}</p>
        <Link to="/skills" className="inline-flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 mt-4 transition-colors">
          <ArrowLeft size={14} /> 返回列表
        </Link>
      </div>
    )
  }
  if (!skill) {
    return (
      <div className="text-center py-16">
        <p className="text-sm text-zinc-500">未找到技能内容</p>
        <Link to="/skills" className="inline-flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 mt-4 transition-colors">
          <ArrowLeft size={14} /> 返回列表
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <Link to="/skills" className="inline-flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 transition-colors">
        <ArrowLeft size={14} /> 返回列表
      </Link>
      <Card className="p-0 overflow-hidden">
        {/* Frontmatter rendered as YAML code block */}
        <div className="border-b border-zinc-800 bg-zinc-900/80 px-6 py-3">
          <pre className="text-xs text-zinc-400 font-mono leading-relaxed whitespace-pre-wrap">{buildFrontmatter(skill)}</pre>
        </div>
        {/* Skill body rendered as Markdown */}
        <div className="px-6 py-5">
          <MarkdownRenderer content={skill.instructions} />
        </div>
      </Card>
    </div>
  )
}

function buildFrontmatter(skill: SkillDetailType): string {
  let lines = ['---']
  lines.push(`name: ${skill.name}`)
  if (skill.description) {
    lines.push(`description: ${skill.description}`)
  }
  lines.push('---')
  return lines.join('\n')
}

