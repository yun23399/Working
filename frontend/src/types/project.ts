// 最小项目摘要类型，用于阶段一的本地项目切换视图
export interface ProjectSummary {
  id: string
  name: string
  summary: string
  conversationIds: number[]
  updatedAt: string
}
