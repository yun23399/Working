// 工作流预览请求类型
export interface WorkflowPreviewRequest {
  force_replan: boolean
}

// 结构化需求摘要类型
export interface RequirementSummary {
  goal: string
  constraints: string[]
  output_types: string[]
  context: string
}

// 工作流节点类型
export interface WorkflowNode {
  id: string
  role: string
  task: string
  tools: string[]
  llm: string
  max_retries: number
  depends_on: string[]
  runtime_status?: string
}

// 工作流 DAG 类型
export interface WorkflowDag {
  nodes: WorkflowNode[]
  execution_mode: string
}

// 工作流执行日志类型
export interface WorkflowExecutionLog {
  node_id: string
  role: string
  summary: string
  status: string
}

// 工作流预览响应类型
export interface WorkflowPreview {
  workflow_id: number
  conversation_id: number
  status: string
  progress: number
  requirement: RequirementSummary
  dag: WorkflowDag
  execution_logs: WorkflowExecutionLog[]
  created_at: string
  updated_at: string
}
