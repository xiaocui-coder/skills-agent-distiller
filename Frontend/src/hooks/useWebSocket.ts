import { useEffect, useRef } from 'react'
import { WebSocketManager } from '../api/ws'
import { useChatStore } from '../stores/chatStore'
import type { WSEvent } from '../api/types'

export function useWebSocket(url: string) {
  const managerRef = useRef<WebSocketManager | null>(null)
  const setStatus = useChatStore((s) => s.setStatus)
  const addUserMessage = useChatStore((s) => s.addUserMessage)
  const addTextChunk = useChatStore((s) => s.addTextChunk)
  const setThinking = useChatStore((s) => s.setThinking)
  const appendThinking = useChatStore((s) => s.appendThinking)
  const addToolCall = useChatStore((s) => s.addToolCall)
  const setToolResult = useChatStore((s) => s.setToolResult)
  const finalizeMessage = useChatStore((s) => s.finalizeMessage)
  const setError = useChatStore((s) => s.setError)

  useEffect(() => {
    const manager = new WebSocketManager(
      url,
      (event: WSEvent) => {
        switch (event.type) {
          case 'stream_start':
            useChatStore.setState({ isStreaming: true })
            break
          case 'thinking': {
            const { content, id } = event as { content: string; id: number }
            const existing = useChatStore.getState().currentThinking.find((t) => t.id === id)
            if (existing) {
              appendThinking(content, id)
            } else {
              setThinking(content, id)
            }
            break
          }
          case 'text': {
            const content = (event as { content: string }).content
            if (typeof content === 'string') {
              addTextChunk(content)
            }
            break
          }
          case 'tool_call': {
            const e = event as { id: string; name: string; args: Record<string, unknown> }
            if (e.id && e.name) {
              addToolCall({ id: e.id, name: e.name, args: e.args ?? {} })
            }
            break
          }
          case 'tool_result': {
            const e = event as { name: string; content: string; success: boolean }
            setToolResult(e.name, e.content ?? '', e.success ?? true)
            break
          }
          case 'done':
            finalizeMessage((event as { response: string }).response)
            break
          case 'error':
            // Finalize any in-progress streaming content before showing error
            finalizeMessage('')
            setError((event as { message: string }).message)
            break
        }
      },
      (status) => setStatus(status),
    )
    managerRef.current = manager
    manager.connect()

    return () => {
      manager.disconnect()
    }
  }, [url, setStatus, addTextChunk, setThinking, appendThinking, addToolCall, setToolResult, finalizeMessage, setError])

  const send = (content: string, threadId = 'default') => {
    addUserMessage(content)
    managerRef.current?.send({ type: 'message', content, thread_id: threadId })
  }

  const reconnect = () => managerRef.current?.reconnect()

  return { send, reconnect }
}
