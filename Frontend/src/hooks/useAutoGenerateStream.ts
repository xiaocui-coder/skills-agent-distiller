import { useState, useRef, useCallback } from 'react'
import { fetchSSE } from '../api/sse'
import type { AutoGenResult, SSEEvent } from '../api/types'

interface UseAutoGenerateStreamReturn {
  streaming: boolean
  rawText: string
  result: AutoGenResult | null
  error: string | null
  start: (input: string, answers?: string[]) => Promise<void>
  reset: () => void
}

export function useAutoGenerateStream(): UseAutoGenerateStreamReturn {
  const [streaming, setStreaming] = useState(false)
  const [rawText, setRawText] = useState('')
  const [result, setResult] = useState<AutoGenResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const start = useCallback(async (input: string, answers?: string[]) => {
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
      if (answers && answers.length > 0) {
        body.answers = answers
      }
      for await (const event of fetchSSE<AutoGenResult>('/api/distiller/auto-generate', body, ac.signal)) {
        const e = event as SSEEvent<AutoGenResult>
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
