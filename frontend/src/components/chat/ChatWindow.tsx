import { useEffect, useRef } from 'react'
import type { KeyboardEvent } from 'react'
import { ArrowUp, LoaderCircle, Wifi, WifiOff } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { MessageBubble } from './MessageBubble'
import { TokenCounter } from './TokenCounter'
import type { ActivityLog, ChatMessage, SocketStatus } from '../../types/chat'

interface ChatWindowProps {
  draft: string
  errorMessage: string | null
  isBootstrapping: boolean
  isSending: boolean
  isStreaming: boolean
  logs: ActivityLog[]
  messages: ChatMessage[]
  socketStatus: SocketStatus
  onDraftChange: (draft: string) => void
  onSend: () => void
}

function resolveSocketLabel(socketStatus: SocketStatus): string {
  switch (socketStatus) {
    case 'connected':
      return '实时连接已就绪'
    case 'connecting':
      return '正在建立实时连接'
    case 'reconnecting':
      return '实时连接恢复中'
    case 'error':
      return '实时连接不可用'
    default:
      return '等待连接'
  }
}

// 聊天窗口组件，负责展示消息流、日志和输入区域
export function ChatWindow({
  draft,
  errorMessage,
  isBootstrapping,
  isSending,
  isStreaming,
  logs,
  messages,
  socketStatus,
  onDraftChange,
  onSend,
}: ChatWindowProps) {
  const { t } = useTranslation()
  const listRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const container = listRef.current
    if (!container) {
      return
    }

    container.scrollTo({
      top: container.scrollHeight,
      behavior: 'smooth',
    })
  }, [logs, messages])

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      onSend()
    }
  }

  const canSend =
    draft.trim().length > 0 && !isSending && !isBootstrapping && socketStatus === 'connected'

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-line px-6 py-4 text-sm">
        <TokenCounter messages={messages} />
        <div
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs ${
            socketStatus === 'connected'
              ? 'bg-[#e8f5ee] text-[#1d6b49]'
              : socketStatus === 'error'
                ? 'bg-[#fff0ef] text-[#a24545]'
                : 'bg-[#eff2fb] text-[#4b5d99]'
          }`}
        >
          {socketStatus === 'connected' ? (
            <Wifi className="h-3.5 w-3.5" />
          ) : (
            <WifiOff className="h-3.5 w-3.5" />
          )}
          {resolveSocketLabel(socketStatus)}
        </div>
      </div>

      {errorMessage ? (
        <div className="mx-6 mt-4 rounded-[18px] border border-[#e3c2bf] bg-[#fff5f4] px-4 py-3 text-sm text-[#9b4b46]">
          {errorMessage}
        </div>
      ) : null}

      {logs.length > 0 ? (
        <div className="mx-6 mt-4 rounded-[20px] border border-line bg-[#f6f2e9] px-4 py-3">
          <div className="mb-2 text-xs font-medium text-ink-soft">实时日志</div>
          <div className="space-y-2 font-mono text-xs text-ink-soft">
            {logs.map((log) => (
              <div key={log.id} className="flex gap-2">
                <span
                  className={`shrink-0 ${
                    log.level === 'ERROR'
                      ? 'text-[#a24545]'
                      : log.level === 'WARNING'
                        ? 'text-[#8a620b]'
                        : 'text-[#4263eb]'
                  }`}
                >
                  [{log.level}]
                </span>
                <span>{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div ref={listRef} className="flex-1 space-y-6 overflow-y-auto px-6 py-6">
        {isBootstrapping ? (
          <div className="flex h-full items-center justify-center">
            <div className="rounded-[24px] border border-line bg-[#f9f6ef] px-5 py-4 text-sm text-ink-soft">
              正在加载会话与历史消息...
            </div>
          </div>
        ) : null}

        {!isBootstrapping && messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="max-w-md rounded-[24px] border border-line bg-[#f9f6ef] px-6 py-5 text-center">
              <div className="text-base font-medium text-ink">当前对话还没有消息</div>
              <p className="mt-3 text-sm leading-7 text-ink-soft">
                输入你的任务需求后，Manager 会通过 WebSocket 以流式方式返回回复。
              </p>
            </div>
          </div>
        ) : null}

        {!isBootstrapping
          ? messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))
          : null}
      </div>

      <div className="border-t border-line px-6 py-4">
        <div className="flex items-end gap-3">
          <textarea
            value={draft}
            onChange={(event) => onDraftChange(event.target.value)}
            onKeyDown={handleKeyDown}
            className="min-h-[56px] flex-1 rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-accent"
            placeholder={t('chat.placeholder')}
          />
          <button
            type="button"
            onClick={onSend}
            disabled={!canSend}
            className="flex h-12 w-12 items-center justify-center rounded-2xl bg-ink text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSending || isStreaming ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowUp className="h-4 w-4" />
            )}
          </button>
        </div>
        <div className="mt-3 text-xs text-ink-faint">
          {socketStatus === 'connected'
            ? 'Enter 发送，Shift + Enter 换行'
            : '等待实时连接建立后即可发送消息'}
        </div>
      </div>
    </div>
  )
}
