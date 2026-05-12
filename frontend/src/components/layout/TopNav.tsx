import { Bell, Search, Settings, User } from 'lucide-react'

const actions = [Search, Bell, Settings, User]

// 顶部导航组件，展示项目标题和全局操作入口
export function TopNav() {
  return (
    <header className="col-span-2 flex items-center justify-between border-b border-line px-6">
      <div className="text-lg font-semibold text-ink">
        AgentFlow <span className="font-normal text-ink-faint">/ 电商网站项目</span>
      </div>
      <div className="flex gap-3">
        {actions.map((Icon, index) => (
          <button
            key={index}
            type="button"
            className="flex h-10 w-10 items-center justify-center rounded-2xl border border-line bg-surface-panel text-ink transition hover:bg-surface-muted"
          >
            <Icon className="h-4 w-4" />
          </button>
        ))}
      </div>
    </header>
  )
}
