import { requestJson } from './client'
import type { InstalledPlugin, PluginSettingsDraft } from '../types/plugin'

// 读取当前仓库已安装插件列表
export async function fetchInstalledPlugins(token: string): Promise<InstalledPlugin[]> {
  return requestJson<InstalledPlugin[]>('/api/system-settings/plugins', {
    token,
  })
}

// 更新指定插件的启停状态
export async function updateInstalledPlugin(
  token: string,
  pluginId: string,
  payload: PluginSettingsDraft,
): Promise<InstalledPlugin> {
  return requestJson<InstalledPlugin>(`/api/system-settings/plugins/${pluginId}`, {
    method: 'PUT',
    token,
    body: payload,
  })
}
