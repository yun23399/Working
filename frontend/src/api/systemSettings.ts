import { requestJson } from './client'
import type {
  SystemRuntimeSettings,
  SystemRuntimeSettingsDraft,
} from '../types/systemSettings'

// 读取当前系统运行配置，供设置页展示并发上限和活动槽位
export async function fetchSystemRuntimeSettings(
  token: string,
): Promise<SystemRuntimeSettings> {
  return requestJson<SystemRuntimeSettings>('/api/system-settings/runtime', {
    token,
  })
}

// 更新系统运行配置，当前用于修改工作流并发上限
export async function updateSystemRuntimeSettings(
  token: string,
  payload: SystemRuntimeSettingsDraft,
): Promise<SystemRuntimeSettings> {
  return requestJson<SystemRuntimeSettings>('/api/system-settings/runtime', {
    method: 'PUT',
    token,
    body: payload,
  })
}
