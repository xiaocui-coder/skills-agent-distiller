import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  listSamples, getSample, postAutoClarify,
  listStoreSkills, getStoreSkill, deleteStoreSkill,
  listExportTargets,
} from '../api/rest'

export const useSamples = () =>
  useQuery({
    queryKey: ['distiller', 'samples'],
    queryFn: listSamples,
  })

export const useSample = (key: string) =>
  useQuery({
    queryKey: ['distiller', 'samples', key],
    queryFn: () => getSample(key),
    enabled: !!key,
  })

export const useAutoClarify = () =>
  useMutation({
    mutationFn: (input: string) => postAutoClarify(input),
  })

export const useStoreSkills = () =>
  useQuery({
    queryKey: ['distiller', 'store'],
    queryFn: listStoreSkills,
  })

export const useStoreSkill = (id: string) =>
  useQuery({
    queryKey: ['distiller', 'store', id],
    queryFn: () => getStoreSkill(id),
    enabled: !!id,
  })

export const useDeleteStoreSkill = () => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteStoreSkill(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['distiller', 'store'] }),
  })
}

export const useExportTargets = () =>
  useQuery({
    queryKey: ['distiller', 'targets'],
    queryFn: listExportTargets,
  })
