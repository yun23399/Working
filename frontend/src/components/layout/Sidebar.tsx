import { Folder, MessageSquare, Plus } from 'lucide-react'

const projects = ['电商网站项目', '内容运营助手', '数据分析看板']
const conversations = ['商品页开发', '首页 Banner 设计', '购物车逻辑', 'SEO 优化方案']

// 左侧边栏组件，展示项目与历史对话列表
export function Sidebar() {
  return (
    <aside className="row-start-2 flex flex-col border-r border-line bg-[#f3efe7]">
      <div className="p-4">
        <button
          type="button"
          className="flex w-full items-center gap-2 rounded-2xl border border-line bg-surface-panel px-4 py-4 text-left text-base text-ink transition hover:bg-surface-muted"
        >
          <Plus className="h-4 w-4" />
          新建对话
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
      <div className="space-y-1 px-2">
        {conversations.map((conversation, index) => (
          <button
            key={conversation}
            type="button"
            className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left text-base ${
              index === 0 ? 'bg-surface-panel text-ink' : 'text-ink-soft hover:bg-surface-panel'
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            <span className="flex-1">{conversation}</span>
            {index === 0 ? (
              <span className="rounded-full bg-[#dbe3ff] px-2 py-1 text-xs text-[#4263eb]">进行中</span>
            ) : null}
          </button>
        ))}
      </div>
    </aside>
  )
}
