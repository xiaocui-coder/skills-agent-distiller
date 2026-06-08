import { create } from 'zustand'

export interface ThinkingBlock { id: number; content: string }
export interface ToolCallInfo {
  id: string
  name: string
  args: Record<string, unknown>
  result?: string
  success?: boolean
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  thinking: ThinkingBlock[]
  toolCalls: ToolCallInfo[]
  timestamp: number
}

interface ChatState {
  status: 'connecting' | 'connected' | 'disconnected' | 'reconnecting'
  messages: ChatMessage[]
  currentStreaming: string
  currentThinking: ThinkingBlock[]
  currentToolCalls: ToolCallInfo[]
  isStreaming: boolean
  error: string | null

  setStatus: (s: ChatState['status']) => void
  addUserMessage: (content: string) => void
  addTextChunk: (content: string) => void
  setThinking: (content: string, id: number) => void
  appendThinking: (content: string, id: number) => void
  addToolCall: (tc: ToolCallInfo) => void
  setToolResult: (name: string, content: string, success: boolean) => void
  finalizeMessage: (response: string) => void
  setError: (msg: string) => void
  clearError: () => void
  reset: () => void
}

let msgCounter = 0

export const useChatStore = create<ChatState>((set) => ({
  status: 'disconnected',
  messages: [],
  currentStreaming: '',
  currentThinking: [],
  currentToolCalls: [],
  isStreaming: false,
  error: null,

  setStatus: (status) => set({ status }),

  addUserMessage: (content) => {
    const msg: ChatMessage = {
      id: `msg-${++msgCounter}`,
      role: 'user',
      content,
      thinking: [],
      toolCalls: [],
      timestamp: Date.now(),
    }
    set((s) => ({ messages: [...s.messages, msg] }))
  },

  addTextChunk: (content) =>
    set((s) => ({ currentStreaming: s.currentStreaming + content })),

  setThinking: (content, id) =>
    set((s) => {
      const existing = s.currentThinking.find((t) => t.id === id)
      if (existing) {
        return {
          currentThinking: s.currentThinking.map((t) =>
            t.id === id ? { ...t, content: t.content + content } : t,
          ),
        }
      }
      return { currentThinking: [...s.currentThinking, { id, content }] }
    }),

  appendThinking: (content, id) =>
    set((s) => ({
      currentThinking: s.currentThinking.map((t) =>
        t.id === id ? { ...t, content: t.content + content } : t,
      ),
    })),

  addToolCall: (tc) =>
    set((s) => ({ currentToolCalls: [...s.currentToolCalls, tc] })),

  setToolResult: (name, content, success) =>
    set((s) => ({
      currentToolCalls: s.currentToolCalls.map((tc) =>
        tc.name === name ? { ...tc, result: content, success } : tc,
      ),
    })),

  finalizeMessage: (response) =>
    set((s) => {
      const msg: ChatMessage = {
        id: `msg-${++msgCounter}`,
        role: 'assistant',
        content: response || s.currentStreaming,
        thinking: [...s.currentThinking],
        toolCalls: [...s.currentToolCalls],
        timestamp: Date.now(),
      }
      return {
        messages: [...s.messages, msg],
        currentStreaming: '',
        currentThinking: [],
        currentToolCalls: [],
        isStreaming: false,
      }
    }),

  setError: (msg) => set({ error: msg, isStreaming: false, currentStreaming: '', currentToolCalls: [] }),
  clearError: () => set({ error: null }),
  reset: () =>
    set({
      messages: [],
      currentStreaming: '',
      currentThinking: [],
      currentToolCalls: [],
      isStreaming: false,
      error: null,
    }),
}))
