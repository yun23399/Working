import { requestJson } from './client'
import type {
  AgentRoleTemplate,
  AgentRoleTemplateDraft,
  AgentRoleTemplateExportBundle,
  AgentRoleTemplateImportBundle,
  AgentRoleTemplateImportResponse,
} from '../types/agentRoleTemplate'

// 获取当前用户的全部自定义角色模板
export async function fetchAgentRoleTemplates(
  token: string,
): Promise<AgentRoleTemplate[]> {
  return requestJson<AgentRoleTemplate[]>('/api/agent-role-templates', {
    token,
  })
}

// 创建自定义角色模板
export async function createAgentRoleTemplate(
  token: string,
  payload: AgentRoleTemplateDraft,
): Promise<AgentRoleTemplate> {
  return requestJson<AgentRoleTemplate>('/api/agent-role-templates', {
    method: 'POST',
    token,
    body: payload,
  })
}

// 更新自定义角色模板
export async function updateAgentRoleTemplate(
  token: string,
  templateId: string,
  payload: AgentRoleTemplateDraft,
): Promise<AgentRoleTemplate> {
  return requestJson<AgentRoleTemplate>(`/api/agent-role-templates/${templateId}`, {
    method: 'PUT',
    token,
    body: payload,
  })
}

// 删除自定义角色模板
export async function deleteAgentRoleTemplate(
  token: string,
  templateId: string,
): Promise<void> {
  await requestJson<void>(`/api/agent-role-templates/${templateId}`, {
    method: 'DELETE',
    token,
  })
}

// 导出当前用户的全部自定义角色模板
export async function exportAgentRoleTemplates(
  token: string,
): Promise<AgentRoleTemplateExportBundle> {
  return requestJson<AgentRoleTemplateExportBundle>('/api/agent-role-templates/export', {
    token,
  })
}

// 导入角色模板配置，并按指定策略处理同名角色
export async function importAgentRoleTemplates(
  token: string,
  payload: {
    conflict_strategy: 'skip' | 'overwrite'
    bundle: AgentRoleTemplateImportBundle
  },
): Promise<AgentRoleTemplateImportResponse> {
  return requestJson<AgentRoleTemplateImportResponse>('/api/agent-role-templates/import', {
    method: 'POST',
    token,
    body: payload,
  })
}
