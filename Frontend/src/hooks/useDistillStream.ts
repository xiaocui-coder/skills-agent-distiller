import { useState, useRef, useCallback } from 'react'
import { fetchSSE } from '../api/sse'
import type { DistillResult, SSEEvent } from '../api/types'

interface UseDistillStreamReturn {
  streaming: boolean
  rawText: string
  result: DistillResult | null
  error: string | null
  start: (input: string, baseSkillName?: string) => Promise<void>
  reset: () => void
}

export function useDistillStream(): UseDistillStreamReturn {
  const [streaming, setStreaming] = useState(false)
  const [rawText, setRawText] = useState('')
  const [result, setResult] = useState<DistillResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const start = useCallback(async (input: string, baseSkillName?: string) => {
    abortRef.current?.abort()
    const ac = new AbortController()
    abortRef.current = ac

    setStreaming(true)
    setRawText('')
    setResult(null)
    setError(null)

    let accumulated = ''
    try {
      const body: Record<string, unknown> = { input }
      if (baseSkillName) {
        body.base_skill = { name: baseSkillName }
      }
      for await (const event of fetchSSE<DistillResult>('/api/distiller/distill', body, ac.signal)) {
        const e = event as SSEEvent<DistillResult>
        if (e.type === 'chunk') {
          accumulated += e.content
          setRawText(accumulated)
        } else if (e.type === 'done') {
          setResult(e.result)
        } else if (e.type === 'error') {
          setError(e.message)
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setError((err as Error).message)
      }
    } finally {
      setStreaming(false)
      abortRef.current = null
    }
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setStreaming(false)
    setRawText('')
    setResult(null)
    setError(null)
  }, [])

  return { streaming, rawText, result, error, start, reset }
}
