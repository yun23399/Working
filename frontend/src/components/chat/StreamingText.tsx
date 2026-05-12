interface StreamingTextProps {
  content: string
}

// 流式文本组件，后续接入逐 token 展示效果
export function StreamingText({ content }: StreamingTextProps) {
  return <span>{content}</span>
}
