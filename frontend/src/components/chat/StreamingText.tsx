import { motion } from 'framer-motion'

interface StreamingTextProps {
  content: string
}

// 流式文本组件，用于展示逐段追加的回复内容
export function StreamingText({ content }: StreamingTextProps) {
  return (
    <span className="whitespace-pre-wrap">
      {content}
      <motion.span
        animate={{ opacity: [0.3, 1, 0.3] }}
        transition={{ duration: 1, repeat: Infinity, ease: 'easeInOut' }}
        className="ml-0.5 inline-block h-5 w-[2px] translate-y-1 rounded-full bg-accent"
      />
    </span>
  )
}
