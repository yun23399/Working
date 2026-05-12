import { Folder, MessageSquare, Plus } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { Conversation } from '../../types/chat'
import type { ProjectSummary } from '../../types/project'

interface SidebarProps {
  activeProjectId: string
  conversations: Conversation[]
  activeConversationId: number | null
  isCreatingConversation: boolean
  projects: ProjectSummary[]
  onCreateConversation: () => void
  onSelectProject: (projectId: string) => void
  onSelectConversation: (conversation: Conversation) => void
}

// 左侧边栏组件，展示项目占位信息和真实历史对话列表
export function Sidebar({
  activeProjectId,
  conversations,
  activeConversationId,
  isCreatingConversation,
  projects,
  onCreateConversation,
  onSelectProject,
  onSelectConversation,
}: SidebarProps) {
  const { t } = useTranslation()
  const activeProject = projects.find((project) => project.id === activeProjectId) ?? null

  return (
    <aside className="row-start-2 flex flex-col border-r border-line bg-[#f3efe7]">
      <div className="p-4">
        <button
          type="button"
          onClick={onCreateConversation}
          disabled={isCreatingConversation}
          className="flex w-full items-center gap-2 rounded-2xl border border-line bg-surface-panel px-4 py-4 text-left text-base text-ink transition hover:bg-surface-muted disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Plus className="h-4 w-4" />
          {isCreatingConversation ? '创建中...' : t('nav.newConversation')}
        </button>
      </div>
      <div className="px-4 pb-3 text-sm font-medium text-ink-faint">项目</div>
      <div className="space-y-2 px-2">
        {projects.map((project) => (
          <button
            key={project.id}
            type="button"
            onClick={() => onSelectProject(project.id)}
            className={`w-full rounded-2xl border px-3 py-3 text-left transition ${
              activeProjectId === project.id
                ? 'border-line bg-surface-panel text-ink shadow-sm'
                : 'border-transparent text-ink-soft hover:border-line hover:bg-surface-panel'
            }`}
          >
            <div className="flex items-start gap-3">
              <Folder className="mt-0.5 h-4 w-4 shrink-0" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="truncate text-sm font-medium">{project.name}</span>
                  {activeProjectId === project.id ? (
                    <span className="rounded-full bg-[#dbe3ff] px-2 py-1 text-[11px] text-[#4263eb]">
                      当前
                    </span>
                  ) : null}
                </div>
                <div className="mt-1 text-xs leading-5 text-ink-faint">{project.summary}</div>
              </div>
              <span className="rounded-full bg-[#ebe5d9] px-2 py-1 text-[11px] text-ink-soft">
                {project.conversationIds.length}
              </span>
            </div>
          </button>
        ))}
      </div>
      <div className="mt-5 px-4 pb-2 text-sm font-medium text-ink-faint">
        历史对话
        {activeProject ? (
          <span className="ml-2 text-xs font-normal text-ink-faint">/ {activeProject.name}</span>
        ) : null}
      </div>
      <div className="flex-1 space-y-1 overflow-y-auto px-2 pb-4">
        {conversations.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-line px-3 py-4 text-sm leading-6 text-ink-faint">
            当前项目还没有历史对话。你可以直接创建一条新对话，开始整理这个项目的需求。
          </div>
        ) : null}
        {conversations.map((conversation) => (
          <button
            key={conversation.id}
            type="button"
            onClick={() => onSelectConversation(conversation)}
            className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left text-base ${
              activeConversationId === conversation.id
                ? 'bg-surface-panel text-ink'
                : 'text-ink-soft hover:bg-surface-panel'
            }`}
          >
            <MessageSquare className="h-4 w-4 shrink-0" />
            <span className="flex-1 truncate">{conversation.title}</span>
            {activeConversationId === conversation.id ? (
              <span className="rounded-full bg-[#dbe3ff] px-2 py-1 text-xs text-[#4263eb]">进行中</span>
            ) : null}
          </button>
        ))}
      </div>
    </aside>
  )
}
