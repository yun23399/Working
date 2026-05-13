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
