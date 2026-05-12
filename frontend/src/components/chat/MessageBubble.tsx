interface MessageBubbleProps {
  role: 'manager' | 'user'
  name: string
  content: string
}

// 消息气泡组件，区分用户与 Manager 的展示样式
export function MessageBubble({ role, name, content }: MessageBubbleProps) {
  const isUser = role === 'user'

  return (
    <div className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser ? (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#dce5ff] text-sm font-semibold text-[#4c6ef5]">
          M
        </div>
      ) : null}
      <div className={`max-w-[72%] ${isUser ? 'order-first' : ''}`}>
        <div className={`mb-2 text-sm ${isUser ? 'text-right text-ink-faint' : 'text-ink-soft'}`}>{name}</div>
        <div
          className={`rounded-[22px] border px-5 py-4 text-[15px] leading-7 ${
            isUser ? 'border-[#d9d2c5] bg-[#f5f0e7] text-ink' : 'border-line bg-white text-ink'
          }`}
        >
          {content}
        </div>
      </div>
      {isUser ? (
        <div className="flex h-10 w-10 items-center justify-center rounded-full border border-line bg-surface-panel text-sm text-ink-soft">
          我
        </div>
      ) : null}
    </div>
  )
}
