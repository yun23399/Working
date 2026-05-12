import { motion } from 'framer-motion'
import { StreamingText } from './StreamingText'
import type { ChatMessage } from '../../types/chat'

interface MessageBubbleProps {
  message: ChatMessage
}

// 消息气泡组件，区分用户与 Manager 的展示样式
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const senderName = isUser ? '我' : 'Manager'

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24, ease: 'easeOut' }}
      className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {!isUser ? (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#dce5ff] text-sm font-semibold text-[#4c6ef5]">
          M
        </div>
      ) : null}
      <div className={`max-w-[72%] ${isUser ? 'order-first' : ''}`}>
        <div className={`mb-2 text-sm ${isUser ? 'text-right text-ink-faint' : 'text-ink-soft'}`}>
          {senderName}
        </div>
        <div
          className={`rounded-[22px] border px-5 py-4 text-[15px] leading-7 ${
            isUser ? 'border-[#d9d2c5] bg-[#f5f0e7] text-ink' : 'border-line bg-white text-ink'
          }`}
        >
          {message.isStreaming ? (
            <StreamingText content={message.content} />
          ) : (
            <span className="whitespace-pre-wrap">{message.content}</span>
          )}
        </div>
      </div>
      {isUser ? (
        <div className="flex h-10 w-10 items-center justify-center rounded-full border border-line bg-surface-panel text-sm text-ink-soft">
          我
        </div>
      ) : null}
    </motion.div>
  )
}
