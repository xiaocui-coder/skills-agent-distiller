// ── Health & Config ──
export interface HealthResponse {
  status: string
  agent_ready: boolean
  distiller_ready: boolean
}
export interface ConfigResponse {
  model: string
  thinking_enabled: boolean
  distiller_enabled: boolean
}

// ── Skills ──
export interface SkillSummary {
  name: string
  description: string
  path: string
}
export interface SkillDetail {
  name: string
  description: string
  instructions: string
}

// ── Samples ──
export interface SampleSummary {
  key: string
  title: string
  emoji: string
  hook: string
  expected_skill_name: string
  conversation_length: number
}
export interface SampleDetail {
  key: string
  title: string
  emoji: string
  hook: string
  quote: string
  conversation: string
  expected_skill_name: string
}

// ── SSE Events ──
export interface SSEChunkEvent { type: 'chunk'; content: string }
export interface SSEDoneEvent<T> { type: 'done'; result: T }
export interface SSEErrorEvent { type: 'error'; message: string; raw?: string }
export type SSEEvent<T> = SSEChunkEvent | SSEDoneEvent<T> | SSEErrorEvent

// ── Distill (5-act) ──
export type SignalType = 'preference' | 'constraint' | 'workflow' | 'example'
export interface Signal { text: string; type: SignalType }
export interface Clusters {
  preferences: string[]
  constraints: string[]
  workflows: string[]
  examples: string[]
}
export interface SkillBody { name: string; description: string; body: string }
export interface DistillResult { signals: Signal[]; clusters: Clusters; skill: SkillBody }

// ── Clarify ──
export interface ClarifyQuestion { q: string; recommended_answer: string }
export interface ClarifyResult { questions: ClarifyQuestion[] }

// ── Auto Generate (4-act) ──
export interface Intent {
  domain: string
  primary_task: string
  triggers: string[]
  audience: string
}
export interface ExamplePair { bad: string; good: string; reason: string }
export interface Outline {
  rules: string[]
  examples: ExamplePair[]
  reference_titles: string[]
}
export interface ReferenceSection { title: string; content: string }
export interface ReferenceDoc { title: string; sections: ReferenceSection[] }
export interface AutoGenResult {
  intent: Intent
  outline: Outline
  skill: SkillBody
  reference: ReferenceDoc
}

// ── Lint ──
export type LintLevel = 'ok' | 'warn' | 'error'
export interface LintItem { field: string; level: LintLevel; message: string; rule: string }
export interface LintResult { items: LintItem[]; summary: Record<string, LintLevel> }

// ── Diff ──
export interface DiffRule { section: string; text: string; raw: string }
export interface DiffResult {
  added: DiffRule[]
  removed: DiffRule[]
  kept: DiffRule[]
  stats: { added: number; removed: number; kept: number }
}

// ── Export ──
export interface ExportTarget {
  key: string
  title: string
  emoji: string
  filename: string
  description: string
  hint: string
}
export interface ExportResult { target: string; filename: string; content: string; hint: string }

// ── Store ──
export interface SkillVersion {
  v: number
  description: string
  body: string
  signal_count: number
  added_conversation: string
  created_at: string
}
export interface StoredSkillSummary {
  id: string
  name: string
  scenario: string | null
  source: string
  versions_count: number
  latest_version: number
  created_at: string
}
export interface StoredSkillDetail {
  id: string
  name: string
  scenario: string | null
  source: string
  versions: SkillVersion[]
  created_at: string
}

// ── WebSocket Events ──
export interface WSStreamStart { type: 'stream_start'; thread_id: string }
export interface WSThinking { type: 'thinking'; content: string; id: number }
export interface WSText { type: 'text'; content: string }
export interface WSToolCall { type: 'tool_call'; name: string; args: Record<string, unknown>; id: string }
export interface WSToolResult { type: 'tool_result'; name: string; content: string; success: boolean }
export interface WSDone { type: 'done'; response: string }
export interface WSError { type: 'error'; message: string }
export type WSEvent = WSStreamStart | WSThinking | WSText | WSToolCall | WSToolResult | WSDone | WSError
