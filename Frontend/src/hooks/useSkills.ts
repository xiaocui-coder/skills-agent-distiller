import { useQuery } from '@tanstack/react-query'
import { listSkills, getSkill } from '../api/rest'

export const useSkills = () =>
  useQuery({
    queryKey: ['skills'],
    queryFn: listSkills,
    staleTime: 60_000,
  })

export const useSkill = (name: string) =>
  useQuery({
    queryKey: ['skills', name],
    queryFn: () => getSkill(name),
    enabled: !!name,
  })
