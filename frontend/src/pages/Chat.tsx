import { ChatWindow } from '../components/chat/ChatWindow'
import { MainArea } from '../components/layout/MainArea'
import { Sidebar } from '../components/layout/Sidebar'
import { TopNav } from '../components/layout/TopNav'

// 聊天页骨架，组合顶部导航、侧边栏与聊天主区域
export function Chat() {
  return (
    <main className="min-h-screen p-6">
      <section className="mx-auto grid min-h-[720px] max-w-7xl grid-cols-[280px_1fr] grid-rows-[56px_1fr] overflow-hidden rounded-[28px] border border-line bg-surface-panel shadow-panel">
        <TopNav />
        <Sidebar />
        <MainArea>
          <ChatWindow />
        </MainArea>
      </section>
    </main>
  )
}
