import { apiFetch } from './client'
import type {
  HealthResponse, ConfigResponse, SkillSummary, SkillDetail,
  SampleSummary, SampleDetail, ClarifyResult, LintResult,
  DiffResult, ExportResult, ExportTarget, StoredSkillSummary, StoredSkillDetail,
} from './types'

export const getHealth = () => apiFetch<HealthResponse>('/api/health')
export const getConfig = () => apiFetch<ConfigResponse>('/api/config')
export const listSkills = () => apiFetch<SkillSummary[]>('/api/skills')
export const getSkill = (name: string) => apiFetch<SkillDetail>(`/api/skills/${encodeURIComponent(name)}`)

export const listSamples = () => apiFetch<SampleSummary[]>('/api/distiller/samples')
export const getSample = (key: string) => apiFetch<SampleDetail>(`/api/distiller/samples/${encodeURIComponent(key)}`)

export const postAutoClarify = (input: string) =>
  apiFetch<ClarifyResult>('/api/distiller/auto-clarify', {
    method: 'POST',
    body: JSON.stringify({ input }),
  })

export const postLint = (data: { name: string; description: string; body: string }) =>
  apiFetch<LintResult>('/api/distiller/lint', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const postDiff = (data: { old_body: string; new_body: string }) =>
  apiFetch<DiffResult>('/api/distiller/diff', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const postExport = (data: { skill_name: string; target: string }) =>
  apiFetch<ExportResult>('/api/distiller/export', {
    method: 'POST',
    body: JSON.stringify(data),
  })

export const listStoreSkills = () => apiFetch<StoredSkillSummary[]>('/api/distiller/store/skills')
export const getStoreSkill = (id: string) => apiFetch<StoredSkillDetail>(`/api/distiller/store/skills/${encodeURIComponent(id)}`)
export const deleteStoreSkill = (id: string) =>
  apiFetch<{ status: string; deleted: string }>(`/api/distiller/store/skills/${encodeURIComponent(id)}`, { method: 'DELETE' })

export const listExportTargets = () => apiFetch<ExportTarget[]>('/api/distiller/targets')

export interface SaveSkillParams {
  name: string
  description: string
  body: string
  reference_title?: string
  reference_sections?: { title: string; content: string }[]
}

export interface SaveSkillResult {
  status: string
  saved_files?: string[]
  skill_dir?: string
  message?: string
}

export const postSaveSkill = (data: SaveSkillParams) =>
  apiFetch<SaveSkillResult>('/api/distiller/save-skill', {
    method: 'POST',
    body: JSON.stringify(data),
  })
