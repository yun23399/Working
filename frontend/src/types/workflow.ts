// 工作流预览请求类型
export interface WorkflowPreviewRequest {
  force_replan: boolean
  pause_after_nodes: string[]
}

// 工作流控制请求类型
export interface WorkflowControlRequest {
  action: 'pause' | 'resume' | 'abort' | 'redirect'
  redirect_instruction?: string
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
  template_id: string
  template_source: string
  template_summary: string
  role: string
  task: string
  tools: string[]
  llm: string
  max_retries: number
  depends_on: string[]
  trigger_keywords: string[]
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
  artifacts: string[]
}

// 工作流产物预览类型
export type WorkflowArtifactPreviewType = 'code' | 'image' | 'document' | 'binary'

// 工作流产物描述类型
export interface WorkflowArtifact {
  name: string
  relative_path: string
  preview_type: WorkflowArtifactPreviewType
  mime_type: string
  size_bytes: number
  updated_at: string
}

// 工作流交接记录类型
export interface WorkflowHandoffLog {
  from_agent: string
  to_agent: string
  summary: string
  artifacts: string[]
  created_at: string
}

// 工作流共享工作区状态类型
export interface WorkflowWorkspaceState {
  workspace_path: string
  status: string
  progress: number
  active_node_id: string | null
  artifacts: string[]
  updated_at: string
  pause_after_nodes: string[]
}

// 项目级记忆中的最近错误摘要
export interface WorkflowProjectMemoryError {
  workflow_id: number
  node_id: string
  role: string
  error_message: string
  recovery_suggestion: string
  updated_at: string
}

// 项目级记忆类型
export interface WorkflowProjectMemory {
  memory_path: string
  latest_goal: string
  active_constraints: string[]
  key_points: string[]
  artifacts: string[]
  workflow_count: number
  latest_error: WorkflowProjectMemoryError | null
  updated_at: string
}

// 工作流运行状态类型
export interface WorkflowRunState {
  run_id: number | null
  status: string
  control_signal: string
  checkpoint_node_id: string | null
  redirect_instruction: string
  saved_at: string | null
}

// 工作流错误恢复报告类型
export interface WorkflowErrorReport {
  failed_node_id: string
  failed_role: string
  task: string
  error_message: string
  retry_count: number
  max_retries: number
  can_retry: boolean
  upstream_node_id: string | null
  upstream_role: string
  rollback_checkpoint_node_id: string | null
  rollback_progress: number
  recovery_suggestion: string | null
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
  workspace: WorkflowWorkspaceState
  project_memory: WorkflowProjectMemory
  handoff_logs: WorkflowHandoffLog[]
  workflow_run: WorkflowRunState
  error_report: WorkflowErrorReport | null
  created_at: string
  updated_at: string
}
