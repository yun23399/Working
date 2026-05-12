import { create } from 'zustand'

interface ProjectState {
  currentProjectName: string
  setCurrentProjectName: (name: string) => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  currentProjectName: '电商网站项目',
  setCurrentProjectName: (name) => set({ currentProjectName: name }),
}))
