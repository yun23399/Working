// 系统运行配置类型，描述当前并发上限和活动工作流槽位
export interface SystemRuntimeSettings {
  max_concurrent_workflows: number
  active_workflow_count: number
  remaining_slots: number
  is_limit_reached: boolean
}

// 系统运行配置更新请求类型
export interface SystemRuntimeSettingsDraft {
  max_concurrent_workflows: number
}

// 系统 LLM 配置类型，描述当前提供商、模型、超时和密钥状态
export interface SystemLlmSettings {
  provider: string
  model: string
  base_url: string
  timeout_seconds: number
  api_key_configured: boolean
  manager_readiness_threshold: number
}

// 系统 LLM 配置更新请求类型
export interface SystemLlmSettingsDraft {
  provider: string
  model: string
  base_url: string
  api_key: string
  timeout_seconds: number
  manager_readiness_threshold: number
}

// 系统 LLM 连通性测试请求类型
export interface SystemLlmSettingsTestDraft {
  provider: string
  model: string
  base_url: string
  api_key: string
  timeout_seconds: number
}

// 系统 LLM 连通性测试响应类型
export interface SystemLlmSettingsTestResult {
  success: boolean
  runtime_label: string
  message: string
}
