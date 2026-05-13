import { requestJson } from './client'
import type {
  SystemLlmSettings,
  SystemLlmSettingsDraft,
  SystemLlmSettingsTestDraft,
  SystemLlmSettingsTestResult,
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

// 读取当前 LLM / API 配置，供设置页展示和回填
export async function fetchSystemLlmSettings(
  token: string,
): Promise<SystemLlmSettings> {
  return requestJson<SystemLlmSettings>('/api/system-settings/llm', {
    token,
  })
}

// 更新当前 LLM / API 配置
export async function updateSystemLlmSettings(
  token: string,
  payload: SystemLlmSettingsDraft,
): Promise<SystemLlmSettings> {
  return requestJson<SystemLlmSettings>('/api/system-settings/llm', {
    method: 'PUT',
    token,
    body: payload,
  })
}

// 使用临时参数测试当前第三方模型连通性
export async function testSystemLlmSettings(
  token: string,
  payload: SystemLlmSettingsTestDraft,
): Promise<SystemLlmSettingsTestResult> {
  return requestJson<SystemLlmSettingsTestResult>('/api/system-settings/llm/test', {
    method: 'POST',
    token,
    body: payload,
  })
}
