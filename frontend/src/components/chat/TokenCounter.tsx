import { useTranslation } from 'react-i18next'
import type { ChatMessage } from '../../types/chat'

interface TokenCounterProps {
  messages: ChatMessage[]
}

// 统计并展示当前会话累计 Token 数量
export function TokenCounter({ messages }: TokenCounterProps) {
  const { t } = useTranslation()
  const totalTokens = messages.reduce((total, message) => total + message.tokenCount, 0)

  return (
    <div className="text-ink-faint">
      ● {t('chat.tokenUsage')} · {totalTokens} tokens
    </div>
  )
}
