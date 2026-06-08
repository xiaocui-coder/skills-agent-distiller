import { useMatch } from 'react-router-dom'
import { useSkills, useSkill } from '../hooks/useSkills'
import { SkillsList } from '../components/skills/SkillsList'
import { SkillDetail } from '../components/skills/SkillDetail'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'

export function SkillsPage() {
  const match = useMatch('/skills/:name')
  const name = match?.params?.name ?? ''
  const { data: skills, isLoading: listLoading } = useSkills()
  const { data: skill, isLoading: detailLoading, error: detailError } = useSkill(name || '')

  if (name) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <SkillDetail skill={skill} loading={detailLoading} error={detailError} />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-lg font-semibold text-zinc-200 mb-4">技能库</h2>
      {listLoading ? <LoadingSpinner className="py-16" /> : <SkillsList skills={skills || []} />}
    </div>
  )
}
