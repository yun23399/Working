import { MessageBubble } from './MessageBubble'

interface ChatMessage {
  id: string
  role: 'manager' | 'user'
  name: string
  content: string
}

const messages: ChatMessage[] = [
  {
    id: '1',
    role: 'manager',
    name: 'Manager',
    content:
      '你好！我是你的 AI 管理员。请告诉我想完成什么任务，我会帮助你规划并安排合适的 Agent 团队来执行。',
  },
  {
    id: '2',
    role: 'user',
    name: '我',
    content: '帮我做一个电商商品详情页，需要有图片展示、价格、加入购物车功能。',
  },
  {
    id: '3',
    role: 'manager',
    name: 'Manager',
    content: '好的，我来了解一下需求细节。请问技术栈偏好、是否需要真实接口，以及有没有设计参考？',
  },
]

// 聊天窗口组件，展示消息列表与输入区域
export function ChatWindow() {
  return (
    <div className="flex h-full flex-col">
      <div className="px-6 py-4 text-sm text-ink-faint">● 本次会话 · 2,847 tokens</div>
      <div className="flex-1 space-y-6 overflow-y-auto px-6 pb-6">
        {messages.map((message) => (
          <MessageBubble key={message.id} {...message} />
        ))}
      </div>
      <div className="border-t border-line px-6 py-4">
        <div className="flex items-end gap-3">
          <textarea
            className="min-h-[52px] flex-1 rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-accent"
            placeholder="输入消息..."
          />
          <button
            type="button"
            className="flex h-12 w-12 items-center justify-center rounded-2xl bg-ink text-white transition hover:opacity-90"
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  )
}
