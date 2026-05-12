import type { ReactNode } from 'react'

interface MainAreaProps {
  activeConversationTitle: string | null
  children: ReactNode
  conversationCount: number
  projectName: string
  projectSummary: string
}

// 主内容容器，承载聊天与工作流主视图
export function MainArea({
  activeConversationTitle,
  children,
  conversationCount,
  projectName,
  projectSummary,
}: MainAreaProps) {
  return (
    <section className="row-start-2 flex min-h-0 flex-col bg-surface-panel">
      <div className="border-b border-line bg-[linear-gradient(180deg,#fcfbf7_0%,#f7f3eb_100%)] px-6 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="max-w-3xl">
            <div className="text-xs uppercase tracking-[0.22em] text-ink-faint">当前项目</div>
            <h1 className="mt-2 text-2xl font-semibold text-ink">{projectName}</h1>
            <p className="mt-2 text-sm leading-6 text-ink-soft">{projectSummary}</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="min-w-[132px] rounded-[20px] border border-line bg-white/70 px-4 py-3">
              <div className="text-xs text-ink-faint">历史对话数</div>
              <div className="mt-2 text-xl font-semibold text-ink">{conversationCount}</div>
            </div>
            <div className="min-w-[220px] rounded-[20px] border border-line bg-white/70 px-4 py-3">
              <div className="text-xs text-ink-faint">当前会话</div>
              <div className="mt-2 truncate text-sm font-medium text-ink">
                {activeConversationTitle ?? '还没有选中的对话'}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="min-h-0 flex-1">{children}</div>
    </section>
  )
}
