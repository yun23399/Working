import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ArrowRight,
  FolderKanban,
  MessageSquareMore,
  PencilLine,
  Plus,
  Search,
  Trash2,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { fetchCurrentUser } from '../api/auth'
import { ApiRequestError } from '../api/client'
import { fetchConversations } from '../api/conversations'
import { useAuthStore } from '../stores/authStore'
import { useChatStore } from '../stores/chatStore'
import {
  filterConversationsForProject,
  useProjectStore,
} from '../stores/projectStore'
import type { Conversation } from '../types/chat'
import type { ProjectDraft } from '../types/project'

const emptyProjectDraft: ProjectDraft = {
  name: '',
  summary: '',
}

function formatUpdatedAt(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '刚刚更新'
  }

  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function resolveProjectPageError(error: unknown): string {
  if (error instanceof ApiRequestError) {
    return error.message
  }

  return '项目数据加载失败，请稍后重试'
}

// 项目页，负责本地项目分组的搜索、创建、编辑、删除与对话迁移
export function Projects() {
  const navigate = useNavigate()
  const [searchKeyword, setSearchKeyword] = useState('')
  const [projectDraft, setProjectDraft] = useState<ProjectDraft>(emptyProjectDraft)
  const [editingProjectId, setEditingProjectId] = useState<string | null>(null)
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null)
  const [isBootstrapping, setIsBootstrapping] = useState(false)
  const [pageError, setPageError] = useState<string | null>(null)
  const token = useAuthStore((state) => state.token)
  const setUser = useAuthStore((state) => state.setUser)
  const clearSession = useAuthStore((state) => state.clearSession)
  const clearChatState = useChatStore((state) => state.clearChatState)
  const setConversations = useChatStore((state) => state.setConversations)
  const conversations = useChatStore((state) => state.conversations)
  const activeConversationId = useChatStore((state) => state.activeConversationId)
  const setActiveConversationId = useChatStore((state) => state.setActiveConversationId)
  const resetMessages = useChatStore((state) => state.resetMessages)
  const projects = useProjectStore((state) => state.projects)
  const activeProjectId = useProjectStore((state) => state.activeProjectId)
  const setActiveProjectId = useProjectStore((state) => state.setActiveProjectId)
  const syncConversations = useProjectStore((state) => state.syncConversations)
  const createProject = useProjectStore((state) => state.createProject)
  const updateProject = useProjectStore((state) => state.updateProject)
  const deleteProject = useProjectStore((state) => state.deleteProject)
  const moveConversationToProject = useProjectStore((state) => state.moveConversationToProject)

  const handleUnauthorized = useCallback(() => {
    clearSession()
    clearChatState()
    navigate('/login', { replace: true })
  }, [clearChatState, clearSession, navigate])

  useEffect(() => {
    if (!token) {
      navigate('/login', { replace: true })
      return
    }

    let isCurrent = true

    const bootstrapProjects = async () => {
      setIsBootstrapping(true)
      setPageError(null)

      try {
        const [user, nextConversations] = await Promise.all([
          fetchCurrentUser(token),
          fetchConversations(token),
        ])

        if (!isCurrent) {
          return
        }

        setUser(user)
        setConversations(nextConversations)
        syncConversations(nextConversations)
      } catch (error) {
        if (error instanceof ApiRequestError && error.status === 401) {
          handleUnauthorized()
          return
        }

        if (isCurrent) {
          setPageError(resolveProjectPageError(error))
        }
      } finally {
        if (isCurrent) {
          setIsBootstrapping(false)
        }
      }
    }

    if (conversations.length === 0) {
      void bootstrapProjects()
      return () => {
        isCurrent = false
      }
    }

    void bootstrapProjects()

    return () => {
      isCurrent = false
    }
  }, [conversations.length, handleUnauthorized, navigate, setConversations, setUser, syncConversations, token])

  const filteredProjects = useMemo(() => {
    const keyword = searchKeyword.trim().toLowerCase()
    if (!keyword) {
      return projects
    }

    return projects.filter((project) => {
      const searchableText = `${project.name} ${project.summary}`.toLowerCase()
      return searchableText.includes(keyword)
    })
  }, [projects, searchKeyword])

  const selectedConversation = useMemo(() => {
    if (selectedConversationId === null) {
      return null
    }

    return conversations.find((conversation) => conversation.id === selectedConversationId) ?? null
  }, [conversations, selectedConversationId])

  const activeProject = projects.find((project) => project.id === activeProjectId) ?? null

  const handleDraftChange = (field: keyof ProjectDraft, value: string) => {
    setProjectDraft((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const resetProjectEditor = () => {
    setProjectDraft(emptyProjectDraft)
    setEditingProjectId(null)
  }

  const handleCreateProject = () => {
    createProject(projectDraft)
    resetProjectEditor()
    setPageError(null)
  }

  const handleStartEditing = (projectId: string) => {
    const targetProject = projects.find((project) => project.id === projectId)
    if (!targetProject) {
      return
    }

    setEditingProjectId(projectId)
    setProjectDraft({
      name: targetProject.name,
      summary: targetProject.summary,
    })
    setPageError(null)
  }

  const handleSaveProject = () => {
    if (editingProjectId === null) {
      handleCreateProject()
      return
    }

    updateProject(editingProjectId, projectDraft)
    resetProjectEditor()
    setPageError(null)
  }

  const handleDeleteProject = (projectId: string) => {
    if (projects.length <= 1) {
      setPageError('至少需要保留一个项目，当前不能删除最后一个项目。')
      return
    }

    deleteProject(projectId)
    if (editingProjectId === projectId) {
      resetProjectEditor()
    }
    setPageError(null)
  }

  const handleMoveConversation = (targetProjectId: string) => {
    if (selectedConversationId === null) {
      setPageError('请先选择一条要迁移的对话。')
      return
    }

    moveConversationToProject(selectedConversationId, targetProjectId)
    if (targetProjectId !== activeProjectId) {
      setSelectedConversationId(null)
    }
    setPageError(null)
  }

  const handleOpenChat = () => {
    navigate('/chat')
  }

  const handleOpenProjectConversation = (projectId: string, conversation: Conversation) => {
    setActiveProjectId(projectId)
    setActiveConversationId(conversation.id)
    resetMessages()
    navigate('/chat')
  }

  const actionButtonLabel = editingProjectId === null ? '创建项目' : '保存修改'
  const actionButtonDescription =
    editingProjectId === null ? '新建一个本地项目分组，用于管理对话集合。' : '保存当前项目名称与摘要修改。'

  return (
    <main className="min-h-screen px-6 py-8">
      <section className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <div className="rounded-[28px] border border-line bg-surface-panel p-8 shadow-panel">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.24em] text-ink-faint">项目视图</div>
              <h1 className="mt-2 text-3xl font-semibold text-ink">本地多项目管理</h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-ink-soft">
                当前阶段继续沿用前端本地项目实体。你可以在这里搜索项目、创建新项目、修改摘要、删除空余分组，并把已有对话迁移到其它项目。
              </p>
            </div>
            <button
              type="button"
              onClick={handleOpenChat}
              className="flex items-center justify-center gap-2 rounded-2xl border border-line bg-[#1f1c17] px-4 py-3 text-sm text-white transition hover:opacity-90"
            >
              返回工作台
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
            <label className="flex items-center gap-3 rounded-[22px] border border-line bg-white px-4 py-3">
              <Search className="h-4 w-4 text-ink-faint" />
              <input
                value={searchKeyword}
                onChange={(event) => setSearchKeyword(event.target.value)}
                placeholder="搜索项目名称或摘要"
                className="w-full border-none bg-transparent text-sm text-ink outline-none placeholder:text-ink-faint"
              />
            </label>
            <div className="grid grid-cols-3 gap-3 rounded-[22px] border border-line bg-[#fbf8f1] px-4 py-3 text-center">
              <div>
                <div className="text-xs text-ink-faint">项目数</div>
                <div className="mt-1 text-lg font-semibold text-ink">{projects.length}</div>
              </div>
              <div>
                <div className="text-xs text-ink-faint">对话数</div>
                <div className="mt-1 text-lg font-semibold text-ink">{conversations.length}</div>
              </div>
              <div>
                <div className="text-xs text-ink-faint">当前项目</div>
                <div className="mt-1 truncate text-sm font-semibold text-ink">
                  {activeProject?.name ?? '未选择'}
                </div>
              </div>
            </div>
          </div>

          {pageError ? (
            <div className="mt-4 rounded-[20px] border border-[#efc1ba] bg-[#fff3f1] px-4 py-3 text-sm text-[#9f3d2e]">
              {pageError}
            </div>
          ) : null}
        </div>

        <div className="grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
          <aside className="rounded-[28px] border border-line bg-surface-panel p-6 shadow-panel">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#ece7dc] text-ink">
                {editingProjectId === null ? <Plus className="h-5 w-5" /> : <PencilLine className="h-5 w-5" />}
              </div>
              <div>
                <div className="text-base font-semibold text-ink">
                  {editingProjectId === null ? '创建项目' : '编辑项目'}
                </div>
                <div className="mt-1 text-xs leading-5 text-ink-faint">{actionButtonDescription}</div>
              </div>
            </div>

            <div className="mt-5 space-y-4">
              <label className="block">
                <div className="mb-2 text-sm font-medium text-ink">项目名称</div>
                <input
                  value={projectDraft.name}
                  onChange={(event) => handleDraftChange('name', event.target.value)}
                  placeholder="例如：营销落地页改版"
                  className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-[#bda98b]"
                />
              </label>
              <label className="block">
                <div className="mb-2 text-sm font-medium text-ink">项目摘要</div>
                <textarea
                  value={projectDraft.summary}
                  onChange={(event) => handleDraftChange('summary', event.target.value)}
                  placeholder="补充该项目的目标、交付物或协作背景。"
                  rows={5}
                  className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm leading-6 text-ink outline-none transition focus:border-[#bda98b]"
                />
              </label>
            </div>

            <div className="mt-5 flex gap-3">
              <button
                type="button"
                onClick={handleSaveProject}
                className="flex-1 rounded-2xl bg-[#1f1c17] px-4 py-3 text-sm text-white transition hover:opacity-90"
              >
                {actionButtonLabel}
              </button>
              <button
                type="button"
                onClick={resetProjectEditor}
                className="rounded-2xl border border-line px-4 py-3 text-sm text-ink transition hover:bg-[#faf7f1]"
              >
                重置
              </button>
            </div>

            <div className="mt-6 rounded-[24px] border border-dashed border-line bg-[#fbf8f1] p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-ink">
                <MessageSquareMore className="h-4 w-4" />
                对话迁移
              </div>
              <p className="mt-2 text-sm leading-6 text-ink-soft">
                先在右侧选中一条对话，再点击目标项目卡片中的“迁移到此项目”。
              </p>
              <div className="mt-3 rounded-2xl bg-white px-3 py-3 text-sm text-ink-soft">
                {selectedConversation
                  ? `当前已选：#${selectedConversation.id} ${selectedConversation.title}`
                  : '当前未选择对话'}
              </div>
            </div>
          </aside>

          <section className="space-y-4">
            {isBootstrapping ? (
              <div className="rounded-[24px] border border-line bg-surface-panel px-5 py-4 text-sm text-ink-soft shadow-panel">
                正在同步项目和对话数据...
              </div>
            ) : null}

            {filteredProjects.length === 0 ? (
              <div className="rounded-[28px] border border-dashed border-line bg-surface-panel px-6 py-10 text-center text-sm text-ink-soft shadow-panel">
                没有匹配的项目，请调整搜索词或新建一个项目。
              </div>
            ) : null}

            {filteredProjects.map((project) => {
              const projectConversations = filterConversationsForProject(
                projects,
                project.id,
                conversations,
              )
              const isActive = activeProjectId === project.id
              const canDelete = projects.length > 1

              return (
                <article
                  key={project.id}
                  className={`rounded-[28px] border p-6 shadow-panel transition ${
                    isActive
                      ? 'border-line bg-[#f7f2e8]'
                      : 'border-line bg-surface-panel'
                  }`}
                >
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-3">
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#ece7dc] text-ink">
                          <FolderKanban className="h-5 w-5" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <h2 className="text-xl font-semibold text-ink">{project.name}</h2>
                            {isActive ? (
                              <span className="rounded-full bg-[#dbe3ff] px-2.5 py-1 text-xs text-[#4263eb]">
                                当前项目
                              </span>
                            ) : null}
                          </div>
                          <div className="mt-1 text-xs text-ink-faint">
                            最近更新：{formatUpdatedAt(project.updatedAt)}
                          </div>
                        </div>
                      </div>
                      <p className="mt-4 max-w-3xl text-sm leading-7 text-ink-soft">
                        {project.summary}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 xl:w-[280px]">
                      <button
                        type="button"
                        onClick={() => setActiveProjectId(project.id)}
                        className="rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink transition hover:bg-[#faf7f1]"
                      >
                        设为当前项目
                      </button>
                      <button
                        type="button"
                        onClick={() => handleStartEditing(project.id)}
                        className="rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink transition hover:bg-[#faf7f1]"
                      >
                        编辑信息
                      </button>
                      <button
                        type="button"
                        onClick={() => handleMoveConversation(project.id)}
                        disabled={selectedConversationId === null}
                        className="rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink transition hover:bg-[#faf7f1] disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        迁移到此项目
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteProject(project.id)}
                        disabled={!canDelete}
                        className="flex items-center justify-center gap-2 rounded-2xl border border-[#efc1ba] bg-[#fff8f7] px-4 py-3 text-sm text-[#9f3d2e] transition hover:bg-[#fff0ed] disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <Trash2 className="h-4 w-4" />
                        删除项目
                      </button>
                    </div>
                  </div>

                  <div className="mt-5 flex items-center justify-between rounded-[22px] bg-white/80 px-4 py-3">
                    <div className="text-sm text-ink-soft">
                      当前包含 <span className="font-semibold text-ink">{projectConversations.length}</span> 条对话
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setActiveProjectId(project.id)
                        navigate('/chat')
                      }}
                      className="text-sm text-[#6a5a3e] transition hover:text-ink"
                    >
                      进入该项目工作台
                    </button>
                  </div>

                  <div className="mt-4 grid gap-3">
                    {projectConversations.length === 0 ? (
                      <div className="rounded-[22px] border border-dashed border-line px-4 py-5 text-sm leading-6 text-ink-faint">
                        当前项目还没有对话。你可以先切换到这个项目，再从聊天页创建首条对话。
                      </div>
                    ) : null}

                    {projectConversations.map((conversation) => {
                      const isSelected = selectedConversationId === conversation.id
                      const isCurrentConversation = activeConversationId === conversation.id

                      return (
                        <div
                          key={conversation.id}
                          className={`rounded-[22px] border px-4 py-4 transition ${
                            isSelected
                              ? 'border-[#c7b391] bg-[#fbf7ef]'
                              : 'border-line bg-white'
                          }`}
                        >
                          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                            <div className="min-w-0 flex-1">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="text-sm font-medium text-ink">
                                  #{conversation.id} {conversation.title}
                                </span>
                                {isCurrentConversation ? (
                                  <span className="rounded-full bg-[#dbe3ff] px-2 py-1 text-[11px] text-[#4263eb]">
                                    当前对话
                                  </span>
                                ) : null}
                                {isSelected ? (
                                  <span className="rounded-full bg-[#ece7dc] px-2 py-1 text-[11px] text-ink-soft">
                                    已选中待迁移
                                  </span>
                                ) : null}
                              </div>
                              <div className="mt-2 text-xs text-ink-faint">
                                最近活跃：{formatUpdatedAt(conversation.updated_at)}
                              </div>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              <button
                                type="button"
                                onClick={() =>
                                  setSelectedConversationId((current) =>
                                    current === conversation.id ? null : conversation.id,
                                  )
                                }
                                className="rounded-2xl border border-line px-3 py-2 text-sm text-ink transition hover:bg-[#faf7f1]"
                              >
                                {isSelected ? '取消选择' : '选择迁移'}
                              </button>
                              <button
                                type="button"
                                onClick={() => handleOpenProjectConversation(project.id, conversation)}
                                className="rounded-2xl border border-line px-3 py-2 text-sm text-ink transition hover:bg-[#faf7f1]"
                              >
                                打开对话
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </article>
              )
            })}
          </section>
        </div>
      </section>
    </main>
  )
}
