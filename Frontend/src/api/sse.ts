import { API_BASE, ApiError } from './client'
import type { SSEEvent } from './types'

export async function* fetchSSE<T>(
  url: string,
  body: Record<string, unknown>,
  signal?: AbortSignal,
): AsyncGenerator<SSEEvent<T>> {
  const res = await fetch(`${API_BASE}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}))
    throw new ApiError(res.status, res.statusText, errBody)
  }
  if (!res.body) throw new Error('No response body')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (trimmed.startsWith('data: ')) {
          try {
            yield JSON.parse(trimmed.slice(6)) as SSEEvent<T>
          } catch {
            // skip malformed line
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
