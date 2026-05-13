// 插件角色模板摘要类型
export interface PluginTemplateSummary {
  template_id: string
  role_name: string
  summary: string
  trigger_keywords: string[]
  default_tools: string[]
}

// 设置页插件响应类型
export interface InstalledPlugin {
  plugin_id: string
  name: string
  description: string
  version: string
  tools: string[]
  agent_templates: PluginTemplateSummary[]
  source_path: string
  is_enabled: boolean
}

// 插件启停更新请求类型
export interface PluginSettingsDraft {
  is_enabled: boolean
}
