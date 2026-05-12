import type { ReactNode } from 'react'

interface MainAreaProps {
  children: ReactNode
}

// 主内容容器，承载聊天与工作流主视图
export function MainArea({ children }: MainAreaProps) {
  return <section className="row-start-2 flex flex-col bg-surface-panel">{children}</section>
}
