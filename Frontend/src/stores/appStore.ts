import { create } from 'zustand'

interface AppState {
  sidebarOpen: boolean
  toggleSidebar: () => void
  activeDistillerTab: string
  setDistillerTab: (tab: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  activeDistillerTab: 'distill',
  setDistillerTab: (tab) => set({ activeDistillerTab: tab }),
}))
