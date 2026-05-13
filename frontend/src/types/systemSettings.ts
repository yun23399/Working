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
