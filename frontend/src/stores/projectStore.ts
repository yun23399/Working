import { create } from 'zustand'
import type { Conversation } from '../types/chat'
import type { ProjectSummary } from '../types/project'

interface StoredProjectState {
  activeProjectId: string
  projects: ProjectSummary[]
}

interface ProjectState {
  activeProjectId: string
  projects: ProjectSummary[]
  setActiveProjectId: (projectId: string) => void
  syncConversations: (conversations: Conversation[]) => void
  attachConversationToActiveProject: (conversationId: number) => void
}

const projectStorageKey = 'agentflow.project.state'

function buildTimestamp(): string {
  return new Date().toISOString()
}

function buildDefaultProjects(): ProjectSummary[] {
  const timestamp = buildTimestamp()
  return [
    {
      id: 'ecommerce',
      name: '电商网站项目',
      summary: '用于商品详情页、购物车、活动页和营销组件的协作交付。',
      conversationIds: [],
      updatedAt: timestamp,
    },
    {
      id: 'content-ops',
      name: '内容运营助手',
      summary: '沉淀专题页文案、投放节奏和运营复盘的最小协作空间。',
      conversationIds: [],
      updatedAt: timestamp,
    },
    {
      id: 'analytics',
      name: '数据分析看板',
      summary: '管理指标看板、异常巡检和埋点核对需求的对话分组。',
      conversationIds: [],
      updatedAt: timestamp,
    },
  ]
}

function isProjectSummary(value: unknown): value is ProjectSummary {
  if (typeof value !== 'object' || value === null) {
    return false
  }

  const candidate = value as Partial<ProjectSummary>
  return (
    typeof candidate.id === 'string' &&
    typeof candidate.name === 'string' &&
    typeof candidate.summary === 'string' &&
    typeof candidate.updatedAt === 'string' &&
    Array.isArray(candidate.conversationIds) &&
    candidate.conversationIds.every((id) => typeof id === 'number')
  )
}

function isStoredProjectState(value: unknown): value is StoredProjectState {
  if (typeof value !== 'object' || value === null) {
    return false
  }

  const candidate = value as Partial<StoredProjectState>
  return (
    typeof candidate.activeProjectId === 'string' &&
    Array.isArray(candidate.projects) &&
    candidate.projects.every((project) => isProjectSummary(project))
  )
}

function readStoredProjectState(): StoredProjectState {
  const defaultProjects = buildDefaultProjects()

  if (typeof window === 'undefined') {
    return {
      activeProjectId: defaultProjects[0].id,
      projects: defaultProjects,
    }
  }

  const rawValue = window.localStorage.getItem(projectStorageKey)
  if (!rawValue) {
    return {
      activeProjectId: defaultProjects[0].id,
      projects: defaultProjects,
    }
  }

  try {
    const parsed = JSON.parse(rawValue) as unknown
    if (isStoredProjectState(parsed)) {
      return parsed
    }
  } catch {
    window.localStorage.removeItem(projectStorageKey)
  }

  return {
    activeProjectId: defaultProjects[0].id,
    projects: defaultProjects,
  }
}

function persistProjectState(state: StoredProjectState): void {
  if (typeof window === 'undefined') {
    return
  }

  window.localStorage.setItem(projectStorageKey, JSON.stringify(state))
}

function normalizeProjects(projects: ProjectSummary[]): ProjectSummary[] {
  if (projects.length > 0) {
    return projects
  }

  return buildDefaultProjects()
}

function attachConversationToProject(
  projects: ProjectSummary[],
  projectId: string,
  conversationId: number,
): ProjectSummary[] {
  return projects.map((project) => {
    const filteredIds = project.conversationIds.filter((id) => id !== conversationId)

    if (project.id !== projectId) {
      return {
        ...project,
        conversationIds: filteredIds,
      }
    }

    return {
      ...project,
      conversationIds: [conversationId, ...filteredIds],
      updatedAt: buildTimestamp(),
    }
  })
}

function syncProjectsWithConversations(
  projects: ProjectSummary[],
  activeProjectId: string,
  conversations: Conversation[],
): ProjectSummary[] {
  const normalizedProjects = normalizeProjects(projects)
  const validConversationIds = new Set(conversations.map((conversation) => conversation.id))

  const cleanedProjects = normalizedProjects.map((project) => ({
    ...project,
    conversationIds: project.conversationIds.filter(
      (conversationId, index, ids) =>
        validConversationIds.has(conversationId) && ids.indexOf(conversationId) === index,
    ),
  }))

  const activeProjectExists = cleanedProjects.some((project) => project.id === activeProjectId)
  const fallbackProjectId = activeProjectExists ? activeProjectId : cleanedProjects[0].id
  const assignedConversationIds = new Set(
    cleanedProjects.flatMap((project) => project.conversationIds),
  )

  let nextProjects = cleanedProjects
  for (const conversation of conversations) {
    if (assignedConversationIds.has(conversation.id)) {
      continue
    }

    nextProjects = attachConversationToProject(nextProjects, fallbackProjectId, conversation.id)
    assignedConversationIds.add(conversation.id)
  }

  return nextProjects
}

export function getProjectById(
  projects: ProjectSummary[],
  projectId: string | null,
): ProjectSummary | null {
  if (projectId === null) {
    return projects[0] ?? null
  }

  return projects.find((project) => project.id === projectId) ?? null
}

export function findProjectByConversationId(
  projects: ProjectSummary[],
  conversationId: number,
): ProjectSummary | null {
  return (
    projects.find((project) => project.conversationIds.includes(conversationId)) ?? null
  )
}

export function filterConversationsForProject(
  projects: ProjectSummary[],
  projectId: string | null,
  conversations: Conversation[],
): Conversation[] {
  const targetProject = getProjectById(projects, projectId)
  if (!targetProject) {
    return conversations
  }

  const projectConversationIds = new Set(targetProject.conversationIds)
  return conversations.filter((conversation) => projectConversationIds.has(conversation.id))
}

const initialProjectState = readStoredProjectState()

export const useProjectStore = create<ProjectState>((set) => ({
  activeProjectId: initialProjectState.activeProjectId,
  projects: normalizeProjects(initialProjectState.projects),
  setActiveProjectId: (projectId) =>
    set((state) => {
      const nextProjects = normalizeProjects(state.projects)
      const nextActiveProjectId = nextProjects.some((project) => project.id === projectId)
        ? projectId
        : nextProjects[0].id

      persistProjectState({
        activeProjectId: nextActiveProjectId,
        projects: nextProjects,
      })

      return {
        activeProjectId: nextActiveProjectId,
        projects: nextProjects,
      }
    }),
  syncConversations: (conversations) =>
    set((state) => {
      const nextProjects = syncProjectsWithConversations(
        state.projects,
        state.activeProjectId,
        conversations,
      )
      const nextActiveProjectId = nextProjects.some(
        (project) => project.id === state.activeProjectId,
      )
        ? state.activeProjectId
        : nextProjects[0].id

      persistProjectState({
        activeProjectId: nextActiveProjectId,
        projects: nextProjects,
      })

      return {
        activeProjectId: nextActiveProjectId,
        projects: nextProjects,
      }
    }),
  attachConversationToActiveProject: (conversationId) =>
    set((state) => {
      const nextProjects = attachConversationToProject(
        normalizeProjects(state.projects),
        state.activeProjectId,
        conversationId,
      )

      persistProjectState({
        activeProjectId: state.activeProjectId,
        projects: nextProjects,
      })

      return {
        projects: nextProjects,
      }
    }),
}))
