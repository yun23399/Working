import { FolderKanban, LogOut, Settings } from 'lucide-react'
import type { SocketStatus } from '../../types/chat'

interface TopNavProps {
  conversationTitle: string | null
  projectName: string
  username: string | null
  socketStatus: SocketStatus
  onOpenProjects: () => void
  onOpenSettings: () => void
  onLogout: () => void
}

function resolveStatusText(socketStatus: SocketStatus): string {
  switch (socketStatus) {
    case 'connected':
      return '连接稳定'
    case 'reconnecting':
      return '重连中'
    case 'error':
      return '连接异常'
    case 'connecting':
      return '连接中'
    default:
      return '待连接'
  }
}

// 顶部导航组件，展示项目标题、连接状态和退出入口
export function TopNav({
  conversationTitle,
  projectName,
  username,
  socketStatus,
  onOpenProjects,
  onOpenSettings,
  onLogout,
}: TopNavProps) {
  return (
    <header className="col-span-2 flex items-center justify-between border-b border-line bg-[#fbfaf6] px-6 py-3">
      <div>
        <div className="text-lg font-semibold text-ink">
          AgentFlow <span className="font-normal text-ink-faint">/ {projectName}</span>
        </div>
        <div className="mt-1 text-xs text-ink-faint">
          当前会话：{conversationTitle ?? '尚未创建对话'}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div
          className={`rounded-full px-3 py-1 text-xs ${
            socketStatus === 'connected'
              ? 'bg-[#e8f5ee] text-[#1d6b49]'
              : socketStatus === 'error'
                ? 'bg-[#fff0ef] text-[#a24545]'
                : 'bg-[#eef2fb] text-[#51639e]'
          }`}
        >
          {resolveStatusText(socketStatus)}
        </div>
        <button
          type="button"
          onClick={onOpenProjects}
          className="flex items-center gap-2 rounded-2xl border border-line bg-surface-panel px-4 py-2 text-sm text-ink transition hover:bg-surface-muted"
        >
          <FolderKanban className="h-4 w-4" />
          项目页
        </button>
        <button
          type="button"
          onClick={onOpenSettings}
          className="flex h-10 w-10 items-center justify-center rounded-2xl border border-line bg-surface-panel text-ink transition hover:bg-surface-muted"
        >
          <Settings className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={onLogout}
          className="flex items-center gap-2 rounded-2xl border border-line bg-surface-panel px-4 py-2 text-sm text-ink transition hover:bg-surface-muted"
        >
          <LogOut className="h-4 w-4" />
          {username ?? '退出'}
        </button>
      </div>
    </header>
  )
}
