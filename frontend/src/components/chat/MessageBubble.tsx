import { motion } from 'framer-motion'
import { StreamingText } from './StreamingText'
import type { ChatMessage } from '../../types/chat'

interface MessageBubbleProps {
  message: ChatMessage
  searchQuery?: string
  isSearchFocused?: boolean
  isSearchMatch?: boolean
}

// 统一规范化搜索文本，避免大小写差异导致的命中偏差
function normalizeSearchText(value: string): string {
  return value.trim().toLowerCase()
}

// 将文本按关键词拆分，便于渲染高亮片段
function buildHighlightedSegments(
  content: string,
  searchQuery: string,
): Array<{ text: string; matched: boolean }> {
  const normalizedQuery = normalizeSearchText(searchQuery)
  if (normalizedQuery.length === 0) {
    return [{ text: content, matched: false }]
  }

  const lowerContent = content.toLowerCase()
  const segments: Array<{ text: string; matched: boolean }> = []
  let cursor = 0

  while (cursor < content.length) {
    const nextMatchIndex = lowerContent.indexOf(normalizedQuery, cursor)
    if (nextMatchIndex === -1) {
      segments.push({
        text: content.slice(cursor),
        matched: false,
      })
      break
    }

    if (nextMatchIndex > cursor) {
      segments.push({
        text: content.slice(cursor, nextMatchIndex),
        matched: false,
      })
    }

    segments.push({
      text: content.slice(nextMatchIndex, nextMatchIndex + normalizedQuery.length),
      matched: true,
    })
    cursor = nextMatchIndex + normalizedQuery.length
  }

  return segments.length > 0 ? segments : [{ text: content, matched: false }]
}

// 消息气泡组件，区分用户与 Manager 的展示样式
export function MessageBubble({
  message,
  searchQuery = '',
  isSearchFocused = false,
  isSearchMatch = false,
}: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const senderName = isUser ? '我' : 'Manager'
  const highlightSegments = buildHighlightedSegments(message.content, searchQuery)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.24, ease: 'easeOut' }}
      className={`flex gap-4 rounded-[28px] px-2 py-2 transition ${
        isUser ? 'justify-end' : 'justify-start'
      } ${
        isSearchFocused
          ? 'bg-[#fff4d6] shadow-[inset_0_0_0_1px_rgba(194,154,52,0.28)]'
          : isSearchMatch
            ? 'bg-[#fffaf0]'
            : ''
      }`}
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
            <span className="whitespace-pre-wrap">
              {highlightSegments.map((segment, index) =>
                segment.matched ? (
                  <mark
                    key={`${message.id}-segment-${index}`}
                    className="rounded bg-[#fde68a] px-0.5 text-inherit"
                  >
                    {segment.text}
                  </mark>
                ) : (
                  <span key={`${message.id}-segment-${index}`}>{segment.text}</span>
                ),
              )}
            </span>
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
