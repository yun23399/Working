import { create } from 'zustand'
import type { Conversation } from '../types/chat'
import type { ProjectDraft, ProjectSummary } from '../types/project'

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
  createProject: (draft: ProjectDraft) => void
  updateProject: (projectId: string, draft: ProjectDraft) => void
  deleteProject: (projectId: string) => void
  moveConversationToProject: (conversationId: number, projectId: string) => void
}

const projectStorageKey = 'agentflow.project.state'

function buildTimestamp(): string {
  return new Date().toISOString()
}

function sanitizeProjectText(value: string): string {
  return value.trim().replace(/\s+/g, ' ')
}

function buildProjectId(name: string): string {
  const normalized = sanitizeProjectText(name)
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
    .replace(/^-+|-+$/g, '')

  return normalized.length > 0 ? normalized : `project-${Date.now()}`
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

function buildProjectSummary(draft: ProjectDraft, existingIds: Set<string>): ProjectSummary {
  const timestamp = buildTimestamp()
  const sanitizedName = sanitizeProjectText(draft.name)
  const sanitizedSummary = sanitizeProjectText(draft.summary)
  const baseId = buildProjectId(sanitizedName)
  let nextId = baseId
  let suffix = 1

  while (existingIds.has(nextId)) {
    suffix += 1
    nextId = `${baseId}-${suffix}`
  }

  return {
    id: nextId,
    name: sanitizedName,
    summary: sanitizedSummary,
    conversationIds: [],
    updatedAt: timestamp,
  }
}

function resolveProjectDraft(draft: ProjectDraft): ProjectDraft {
  const name = sanitizeProjectText(draft.name)
  const summary = sanitizeProjectText(draft.summary)

  return {
    name: name.length > 0 ? name : '未命名项目',
    summary: summary.length > 0 ? summary : '等待补充项目说明。',
  }
}

function sortProjectsByUpdatedAt(projects: ProjectSummary[]): ProjectSummary[] {
  return [...projects].sort((left, right) => {
    return new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime()
  })
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

function moveConversationBetweenProjects(
  projects: ProjectSummary[],
  projectId: string,
  conversationId: number,
): ProjectSummary[] {
  return attachConversationToProject(projects, projectId, conversationId)
}

function deleteProjectAndReassignConversations(
  projects: ProjectSummary[],
  activeProjectId: string,
  projectId: string,
): { activeProjectId: string; projects: ProjectSummary[] } {
  const normalizedProjects = normalizeProjects(projects)
  if (normalizedProjects.length <= 1) {
    return {
      activeProjectId,
      projects: normalizedProjects,
    }
  }

  const targetProject = normalizedProjects.find((project) => project.id === projectId)
  if (!targetProject) {
    return {
      activeProjectId,
      projects: normalizedProjects,
    }
  }

  const fallbackProject =
    normalizedProjects.find((project) => project.id === activeProjectId && project.id !== projectId) ??
    normalizedProjects.find((project) => project.id !== projectId) ??
    normalizedProjects[0]

  const remainingProjects = normalizedProjects.filter((project) => project.id !== projectId)
  let nextProjects = remainingProjects

  for (const conversationId of targetProject.conversationIds) {
    nextProjects = moveConversationBetweenProjects(
      nextProjects,
      fallbackProject.id,
      conversationId,
    )
  }

  const nextActiveProjectId = activeProjectId === projectId ? fallbackProject.id : activeProjectId

  return {
    activeProjectId: nextActiveProjectId,
    projects: sortProjectsByUpdatedAt(nextProjects),
  }
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
  createProject: (draft) =>
    set((state) => {
      const normalizedProjects = normalizeProjects(state.projects)
      const resolvedDraft = resolveProjectDraft(draft)
      const nextProject = buildProjectSummary(
        resolvedDraft,
        new Set(normalizedProjects.map((project) => project.id)),
      )
      const nextProjects = sortProjectsByUpdatedAt([nextProject, ...normalizedProjects])

      persistProjectState({
        activeProjectId: nextProject.id,
        projects: nextProjects,
      })

      return {
        activeProjectId: nextProject.id,
        projects: nextProjects,
      }
    }),
  updateProject: (projectId, draft) =>
    set((state) => {
      const resolvedDraft = resolveProjectDraft(draft)
      const nextProjects = sortProjectsByUpdatedAt(
        normalizeProjects(state.projects).map((project) =>
          project.id === projectId
            ? {
                ...project,
                name: resolvedDraft.name,
                summary: resolvedDraft.summary,
                updatedAt: buildTimestamp(),
              }
            : project,
        ),
      )

      persistProjectState({
        activeProjectId: state.activeProjectId,
        projects: nextProjects,
      })

      return {
        projects: nextProjects,
      }
    }),
  deleteProject: (projectId) =>
    set((state) => {
      const nextState = deleteProjectAndReassignConversations(
        state.projects,
        state.activeProjectId,
        projectId,
      )

      persistProjectState(nextState)

      return nextState
    }),
  moveConversationToProject: (conversationId, projectId) =>
    set((state) => {
      const normalizedProjects = normalizeProjects(state.projects)
      const targetExists = normalizedProjects.some((project) => project.id === projectId)
      if (!targetExists) {
        return {
          projects: normalizedProjects,
        }
      }

      const nextProjects = sortProjectsByUpdatedAt(
        moveConversationBetweenProjects(normalizedProjects, projectId, conversationId),
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
