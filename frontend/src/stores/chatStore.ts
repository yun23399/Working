import { create } from 'zustand'

interface ChatState {
  isStreaming: boolean
  setStreaming: (isStreaming: boolean) => void
}

export const useChatStore = create<ChatState>((set) => ({
  isStreaming: false,
  setStreaming: (isStreaming) => set({ isStreaming }),
}))
