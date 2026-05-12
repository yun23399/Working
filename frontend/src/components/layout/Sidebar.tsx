import { Folder, MessageSquare, Plus } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { Conversation } from '../../types/chat'

const projects = ['电商网站项目', '内容运营助手', '数据分析看板']

interface SidebarProps {
  conversations: Conversation[]
  activeConversationId: number | null
  isCreatingConversation: boolean
  onCreateConversation: () => void
  onSelectConversation: (conversation: Conversation) => void
}

// 左侧边栏组件，展示项目占位信息和真实历史对话列表
export function Sidebar({
  conversations,
  activeConversationId,
  isCreatingConversation,
  onCreateConversation,
  onSelectConversation,
}: SidebarProps) {
  const { t } = useTranslation()

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
      <div className="space-y-1 px-2">
        {projects.map((project, index) => (
          <button
            key={project}
            type="button"
            className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left text-base ${
              index === 0 ? 'bg-surface-panel text-ink' : 'text-ink-soft hover:bg-surface-panel'
            }`}
          >
            <Folder className="h-4 w-4" />
            {project}
          </button>
        ))}
      </div>
      <div className="mt-5 px-4 pb-3 text-sm font-medium text-ink-faint">历史对话</div>
      <div className="space-y-1 px-2 pb-4">
        {conversations.length === 0 ? (
          <div className="rounded-2xl px-3 py-4 text-sm text-ink-faint">暂无历史对话</div>
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
