// 自定义 Agent 角色模板类型
export interface AgentRoleTemplate {
  template_id: string
  role_name: string
  summary: string
  system_prompt: string
  trigger_keywords: string[]
  default_tools: string[]
  max_retries: number
  is_enabled: boolean
  created_at: string
  updated_at: string
}

// 自定义 Agent 角色模板表单类型
export interface AgentRoleTemplateDraft {
  role_name: string
  summary: string
  system_prompt: string
  trigger_keywords: string[]
  default_tools: string[]
  max_retries: number
  is_enabled: boolean
}

// 自定义角色模板导出条目类型
export interface AgentRoleTemplateExportItem extends AgentRoleTemplate {
  template_id: string
}

// 自定义角色模板导出包类型
export interface AgentRoleTemplateExportBundle {
  version: '1.0'
  exported_at: string
  template_count: number
  templates: AgentRoleTemplateExportItem[]
}

// 导入请求中的单个角色模板条目
export interface AgentRoleTemplateImportItem extends AgentRoleTemplateDraft {
  template_id?: string | null
}

// 自定义角色模板导入包类型
export interface AgentRoleTemplateImportBundle {
  version: '1.0'
  templates: AgentRoleTemplateImportItem[]
}

// 导入结果单条明细
export interface AgentRoleTemplateImportResultItem {
  role_name: string
  template_id: string | null
  status: 'created' | 'updated' | 'skipped'
  message: string
}

// 自定义角色模板导入结果汇总
export interface AgentRoleTemplateImportResponse {
  total_count: number
  created_count: number
  updated_count: number
  skipped_count: number
  results: AgentRoleTemplateImportResultItem[]
}
