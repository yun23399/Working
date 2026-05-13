import { useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowLeft,
  Bot,
  Download,
  FileUp,
  KeyRound,
  Network,
  Package,
  PencilLine,
  Plus,
  Power,
  Save,
  ShieldCheck,
  Trash2,
  WandSparkles,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { fetchInstalledPlugins, updateInstalledPlugin } from '../api/plugins'
import {
  fetchSystemLlmSettings,
  fetchSystemRuntimeSettings,
  testSystemLlmSettings,
  updateSystemLlmSettings,
  updateSystemRuntimeSettings,
} from '../api/systemSettings'
import {
  createAgentRoleTemplate,
  deleteAgentRoleTemplate,
  exportAgentRoleTemplates,
  fetchAgentRoleTemplates,
  importAgentRoleTemplates,
  updateAgentRoleTemplate,
} from '../api/agentRoleTemplates'
import { ApiRequestError } from '../api/client'
import { fetchCurrentUser } from '../api/auth'
import { useAuthStore } from '../stores/authStore'
import { downloadBlobFile } from '../utils/export'
import type {
  AgentRoleTemplate,
  AgentRoleTemplateDraft,
  AgentRoleTemplateImportBundle,
  AgentRoleTemplateImportResponse,
} from '../types/agentRoleTemplate'
import type { InstalledPlugin } from '../types/plugin'
import type {
  SystemLlmSettings,
  SystemLlmSettingsDraft,
  SystemLlmSettingsTestResult,
  SystemRuntimeSettings,
} from '../types/systemSettings'

const supportedTools = [
  { id: 'file_tool', label: '文件工具' },
  { id: 'api_caller', label: '接口调用' },
  { id: 'browser_tool', label: '浏览器工具' },
  { id: 'image_tool', label: '图像工具' },
  { id: 'code_executor', label: '代码执行' },
]

const emptyRoleDraft: AgentRoleTemplateDraft = {
  role_name: '',
  summary: '',
  system_prompt: '',
  trigger_keywords: [],
  default_tools: ['file_tool'],
  max_retries: 2,
  is_enabled: true,
}

const defaultLlmDraft: SystemLlmSettingsDraft = {
  provider: 'openai',
  model: 'gpt-5.4',
  base_url: '',
  api_key: '',
  timeout_seconds: 60,
  manager_readiness_threshold: 85,
}

function resolveSettingsError(error: unknown): string {
  if (error instanceof ApiRequestError) {
    return error.message
  }

  return '设置操作失败，请稍后重试'
}

function parseKeywordInput(value: string): string[] {
  return value
    .split(/[\n,，]/)
    .map((keyword) => keyword.trim())
    .filter((keyword, index, keywords) => keyword.length > 0 && keywords.indexOf(keyword) === index)
}

function parseConcurrencyLimitInput(value: string): number | null {
  const normalizedValue = value.trim()
  if (!/^\d+$/.test(normalizedValue)) {
    return null
  }

  const parsedValue = Number(normalizedValue)
  if (!Number.isInteger(parsedValue) || parsedValue < 1 || parsedValue > 10) {
    return null
  }

  return parsedValue
}

function formatUpdatedAt(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

// 设置页，负责管理用户级自定义 Agent 角色模板
export function Settings() {
  const navigate = useNavigate()
  const importFileInputRef = useRef<HTMLInputElement | null>(null)
  const token = useAuthStore((state) => state.token)
  const setUser = useAuthStore((state) => state.setUser)
  const clearSession = useAuthStore((state) => state.clearSession)
  const [templates, setTemplates] = useState<AgentRoleTemplate[]>([])
  const [draft, setDraft] = useState<AgentRoleTemplateDraft>(emptyRoleDraft)
  const [editingTemplateId, setEditingTemplateId] = useState<string | null>(null)
  const [keywordInput, setKeywordInput] = useState('')
  const [pageError, setPageError] = useState<string | null>(null)
  const [isBootstrapping, setIsBootstrapping] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isDeletingTemplateId, setIsDeletingTemplateId] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [runtimeSettings, setRuntimeSettings] = useState<SystemRuntimeSettings | null>(null)
  const [llmSettings, setLlmSettings] = useState<SystemLlmSettings | null>(null)
  const [llmDraft, setLlmDraft] = useState<SystemLlmSettingsDraft>(defaultLlmDraft)
  const [isSavingLlmSettings, setIsSavingLlmSettings] = useState(false)
  const [isTestingLlmSettings, setIsTestingLlmSettings] = useState(false)
  const [llmTestResult, setLlmTestResult] = useState<SystemLlmSettingsTestResult | null>(null)
  const [plugins, setPlugins] = useState<InstalledPlugin[]>([])
  const [concurrencyLimitInput, setConcurrencyLimitInput] = useState('3')
  const [isSavingConcurrencyLimit, setIsSavingConcurrencyLimit] = useState(false)
  const [togglingPluginId, setTogglingPluginId] = useState<string | null>(null)
  const [importConflictStrategy, setImportConflictStrategy] = useState<'skip' | 'overwrite'>(
    'skip',
  )
  const [importResult, setImportResult] = useState<AgentRoleTemplateImportResponse | null>(null)

  useEffect(() => {
    if (!token) {
      navigate('/login', { replace: true })
      return
    }

    let isCurrent = true

    const bootstrapSettings = async () => {
      setIsBootstrapping(true)
      setPageError(null)

      try {
        const [
          user,
          roleTemplates,
          runtimeSettingsSnapshot,
          llmSettingsSnapshot,
          installedPlugins,
        ] = await Promise.all([
          fetchCurrentUser(token),
          fetchAgentRoleTemplates(token),
          fetchSystemRuntimeSettings(token),
          fetchSystemLlmSettings(token),
          fetchInstalledPlugins(token),
        ])
        if (!isCurrent) {
          return
        }

        setUser(user)
        setTemplates(roleTemplates)
        setRuntimeSettings(runtimeSettingsSnapshot)
        setLlmSettings(llmSettingsSnapshot)
        setLlmDraft({
          provider: llmSettingsSnapshot.provider,
          model: llmSettingsSnapshot.model,
          base_url: llmSettingsSnapshot.base_url,
          api_key: '',
          timeout_seconds: llmSettingsSnapshot.timeout_seconds,
          manager_readiness_threshold: llmSettingsSnapshot.manager_readiness_threshold,
        })
        setPlugins(installedPlugins)
        setConcurrencyLimitInput(
          String(runtimeSettingsSnapshot.max_concurrent_workflows),
        )
      } catch (error) {
        if (error instanceof ApiRequestError && error.status === 401) {
          clearSession()
          navigate('/login', { replace: true })
          return
        }

        if (isCurrent) {
          setPageError(resolveSettingsError(error))
        }
      } finally {
        if (isCurrent) {
          setIsBootstrapping(false)
        }
      }
    }

    void bootstrapSettings()

    return () => {
      isCurrent = false
    }
  }, [clearSession, navigate, setUser, token])

  const parsedConcurrencyLimit = parseConcurrencyLimitInput(concurrencyLimitInput)

  const enabledTemplateCount = useMemo(() => {
    return templates.filter((template) => template.is_enabled).length
  }, [templates])

  const enabledPluginCount = useMemo(() => {
    return plugins.filter((plugin) => plugin.is_enabled).length
  }, [plugins])

  const handleDraftChange = <K extends keyof AgentRoleTemplateDraft>(
    field: K,
    value: AgentRoleTemplateDraft[K],
  ) => {
    setDraft((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const resetDraft = () => {
    setDraft(emptyRoleDraft)
    setKeywordInput('')
    setEditingTemplateId(null)
    setPageError(null)
  }

  const reloadTemplates = async (authToken: string) => {
    const roleTemplates = await fetchAgentRoleTemplates(authToken)
    setTemplates(roleTemplates)
  }

  const handleTogglePlugin = async (plugin: InstalledPlugin) => {
    if (!token) {
      clearSession()
      navigate('/login', { replace: true })
      return
    }

    setTogglingPluginId(plugin.plugin_id)
    setPageError(null)

    try {
      const updatedPlugin = await updateInstalledPlugin(token, plugin.plugin_id, {
        is_enabled: !plugin.is_enabled,
      })
      setPlugins((current) =>
        current.map((item) =>
          item.plugin_id === updatedPlugin.plugin_id ? updatedPlugin : item,
        ),
      )
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        clearSession()
        navigate('/login', { replace: true })
        return
      }

      setPageError(resolveSettingsError(error))
    } finally {
      setTogglingPluginId(null)
    }
  }

  const handleSaveConcurrencyLimit = async () => {
    if (!token) {
      clearSession()
      navigate('/login', { replace: true })
      return
    }

    if (parsedConcurrencyLimit === null) {
      setPageError('工作流并发上限必须是 1 到 10 之间的整数')
      return
    }

    if (
      runtimeSettings !== null &&
      parsedConcurrencyLimit === runtimeSettings.max_concurrent_workflows
    ) {
      return
    }

    setIsSavingConcurrencyLimit(true)
    setPageError(null)

    try {
      const nextRuntimeSettings = await updateSystemRuntimeSettings(token, {
        max_concurrent_workflows: parsedConcurrencyLimit,
      })
      setRuntimeSettings(nextRuntimeSettings)
      setConcurrencyLimitInput(String(nextRuntimeSettings.max_concurrent_workflows))
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        clearSession()
        navigate('/login', { replace: true })
        return
      }

      setPageError(resolveSettingsError(error))
    } finally {
      setIsSavingConcurrencyLimit(false)
    }
  }

  const handleLlmDraftChange = <K extends keyof SystemLlmSettingsDraft>(
    field: K,
    value: SystemLlmSettingsDraft[K],
  ) => {
    setLlmDraft((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const handleSaveLlmSettings = async () => {
    if (!token) {
      clearSession()
      navigate('/login', { replace: true })
      return
    }

    setIsSavingLlmSettings(true)
    setPageError(null)

    try {
      const nextSettings = await updateSystemLlmSettings(token, llmDraft)
      setLlmSettings(nextSettings)
      setLlmDraft((current) => ({
        ...current,
        api_key: '',
        provider: nextSettings.provider,
        model: nextSettings.model,
        base_url: nextSettings.base_url,
        timeout_seconds: nextSettings.timeout_seconds,
        manager_readiness_threshold: nextSettings.manager_readiness_threshold,
      }))
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        clearSession()
        navigate('/login', { replace: true })
        return
      }

      setPageError(resolveSettingsError(error))
    } finally {
      setIsSavingLlmSettings(false)
    }
  }

  const handleTestLlmSettings = async () => {
    if (!token) {
      clearSession()
      navigate('/login', { replace: true })
      return
    }

    setIsTestingLlmSettings(true)
    setPageError(null)
    setLlmTestResult(null)

    try {
      const result = await testSystemLlmSettings(token, {
        provider: llmDraft.provider,
        model: llmDraft.model,
        base_url: llmDraft.base_url,
        api_key: llmDraft.api_key,
        timeout_seconds: llmDraft.timeout_seconds,
      })
      setLlmTestResult(result)
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        clearSession()
        navigate('/login', { replace: true })
        return
      }

      setPageError(resolveSettingsError(error))
    } finally {
      setIsTestingLlmSettings(false)
    }
  }

  const handleToggleTool = (toolId: string) => {
    const nextTools = draft.default_tools.includes(toolId)
      ? draft.default_tools.filter((tool) => tool !== toolId)
      : [...draft.default_tools, toolId]
    handleDraftChange('default_tools', nextTools.length > 0 ? nextTools : ['file_tool'])
  }

  const handleSubmit = async () => {
    if (!token) {
      clearSession()
      navigate('/login', { replace: true })
      return
    }

    const payload: AgentRoleTemplateDraft = {
      ...draft,
      trigger_keywords: parseKeywordInput(keywordInput),
    }

    setIsSubmitting(true)
    setPageError(null)

    try {
      const nextTemplate =
        editingTemplateId === null
          ? await createAgentRoleTemplate(token, payload)
          : await updateAgentRoleTemplate(token, editingTemplateId, payload)

      setTemplates((current) => {
        const nextTemplates = current.filter(
          (template) => template.template_id !== nextTemplate.template_id,
        )
        return [nextTemplate, ...nextTemplates]
      })
      resetDraft()
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        clearSession()
        navigate('/login', { replace: true })
        return
      }

      setPageError(resolveSettingsError(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleStartEditing = (template: AgentRoleTemplate) => {
    setEditingTemplateId(template.template_id)
    setDraft({
      role_name: template.role_name,
      summary: template.summary,
      system_prompt: template.system_prompt,
      trigger_keywords: template.trigger_keywords,
      default_tools: template.default_tools,
      max_retries: template.max_retries,
      is_enabled: template.is_enabled,
    })
    setKeywordInput(template.trigger_keywords.join(', '))
    setPageError(null)
  }

  const handleDeleteTemplate = async (templateId: string) => {
    if (!token) {
      clearSession()
      navigate('/login', { replace: true })
      return
    }

    setIsDeletingTemplateId(templateId)
    setPageError(null)

    try {
      await deleteAgentRoleTemplate(token, templateId)
      setTemplates((current) =>
        current.filter((template) => template.template_id !== templateId),
      )
      if (editingTemplateId === templateId) {
        resetDraft()
      }
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        clearSession()
        navigate('/login', { replace: true })
        return
      }

      setPageError(resolveSettingsError(error))
    } finally {
      setIsDeletingTemplateId(null)
    }
  }

  const buildExportFileName = () => {
    const timestamp = new Intl.DateTimeFormat('sv-SE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
      .format(new Date())
      .replace(/[-: ]/g, '')
    return `agent-role-templates-${timestamp}.json`
  }

  const handleExportTemplates = async () => {
    if (!token) {
      clearSession()
      navigate('/login', { replace: true })
      return
    }

    setIsExporting(true)
    setPageError(null)

    try {
      const bundle = await exportAgentRoleTemplates(token)
      const fileContent = `${JSON.stringify(bundle, null, 2)}\n`
      downloadBlobFile(
        new Blob([fileContent], { type: 'application/json;charset=utf-8' }),
        buildExportFileName(),
      )
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        clearSession()
        navigate('/login', { replace: true })
        return
      }

      setPageError(resolveSettingsError(error))
    } finally {
      setIsExporting(false)
    }
  }

  const handleOpenImportFilePicker = () => {
    importFileInputRef.current?.click()
  }

  const handleImportTemplates = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    if (!token) {
      clearSession()
      navigate('/login', { replace: true })
      return
    }

    const selectedFile = event.target.files?.[0]
    event.target.value = ''
    if (!selectedFile) {
      return
    }

    setIsImporting(true)
    setPageError(null)

    try {
      const fileText = await selectedFile.text()
      const parsedBundle = JSON.parse(fileText) as AgentRoleTemplateImportBundle
      const result = await importAgentRoleTemplates(token, {
        conflict_strategy: importConflictStrategy,
        bundle: parsedBundle,
      })
      setImportResult(result)
      await reloadTemplates(token)
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        clearSession()
        navigate('/login', { replace: true })
        return
      }

      if (error instanceof SyntaxError) {
        setPageError('导入文件不是合法的 JSON，请重新选择导出的角色模板文件')
      } else {
        setPageError(resolveSettingsError(error))
      }
    } finally {
      setIsImporting(false)
    }
  }

  const handleToggleTemplate = async (template: AgentRoleTemplate) => {
    if (!token) {
      clearSession()
      navigate('/login', { replace: true })
      return
    }

    setPageError(null)

    try {
      const updatedTemplate = await updateAgentRoleTemplate(token, template.template_id, {
        role_name: template.role_name,
        summary: template.summary,
        system_prompt: template.system_prompt,
        trigger_keywords: template.trigger_keywords,
        default_tools: template.default_tools,
        max_retries: template.max_retries,
        is_enabled: !template.is_enabled,
      })
      setTemplates((current) =>
        current.map((item) =>
          item.template_id === updatedTemplate.template_id ? updatedTemplate : item,
        ),
      )
      if (editingTemplateId === updatedTemplate.template_id) {
        setDraft((current) => ({
          ...current,
          is_enabled: updatedTemplate.is_enabled,
        }))
      }
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        clearSession()
        navigate('/login', { replace: true })
        return
      }

      setPageError(resolveSettingsError(error))
    }
  }

  return (
    <main className="min-h-screen bg-[linear-gradient(180deg,#faf7f0_0%,#f2ece2_100%)] px-6 py-8">
      <section className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <div className="rounded-[28px] border border-line bg-surface-panel p-8 shadow-panel">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.24em] text-ink-faint">设置页</div>
              <h1 className="mt-2 text-3xl font-semibold text-ink">用户自定义 Agent 角色管理</h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-ink-soft">
                在这里维护属于当前账号的自定义角色模板。启用后的角色会在重新规划工作流时按触发关键词自动加入节点链路，并沿用你配置的职责、提示词和工具集。
              </p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/chat')}
              className="inline-flex items-center gap-2 rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink transition hover:bg-[#faf7f1]"
            >
              <ArrowLeft className="h-4 w-4" />
              返回工作台
            </button>
          </div>

          <input
            ref={importFileInputRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={(event) => {
              void handleImportTemplates(event)
            }}
          />

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className="rounded-[22px] border border-line bg-white/80 px-4 py-4">
              <div className="text-xs text-ink-faint">当前模型</div>
              <div className="mt-2 text-lg font-semibold text-ink">
                {llmSettings?.model ?? '未配置'}
              </div>
            </div>
            <div className="rounded-[22px] border border-line bg-white/80 px-4 py-4">
              <div className="text-xs text-ink-faint">API 状态</div>
              <div className="mt-2 text-lg font-semibold text-ink">
                {llmSettings?.api_key_configured ? '已配置密钥' : '未配置密钥'}
              </div>
            </div>
            <div className="rounded-[22px] border border-line bg-white/80 px-4 py-4">
              <div className="text-xs text-ink-faint">总代理开始阈值</div>
              <div className="mt-2 text-lg font-semibold text-ink">
                {llmSettings?.manager_readiness_threshold ?? '--'}%
              </div>
            </div>
            <div className="rounded-[22px] border border-line bg-white/80 px-4 py-4">
              <div className="text-xs text-ink-faint">角色模板总数</div>
              <div className="mt-2 text-2xl font-semibold text-ink">{templates.length}</div>
            </div>
            <div className="rounded-[22px] border border-line bg-white/80 px-4 py-4">
              <div className="text-xs text-ink-faint">启用中</div>
              <div className="mt-2 text-2xl font-semibold text-ink">{enabledTemplateCount}</div>
            </div>
            <div className="rounded-[22px] border border-line bg-white/80 px-4 py-4">
              <div className="text-xs text-ink-faint">已启用插件</div>
              <div className="mt-2 text-2xl font-semibold text-ink">{enabledPluginCount}</div>
            </div>
            <div className="rounded-[22px] border border-line bg-white/80 px-4 py-4 md:col-span-3">
              <div className="text-xs text-ink-faint">推荐做法</div>
              <div className="mt-2 text-sm leading-6 text-ink-soft">
                插件适合沉淀可复用的长期角色能力，自定义角色适合维护当前账号的个性化选角规则。
              </div>
            </div>
          </div>

          <div className="mt-6 flex flex-col gap-4 rounded-[24px] border border-line bg-white/70 px-5 py-5">
            <div className="rounded-[22px] border border-line bg-[#faf7f1] px-4 py-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="flex items-center gap-2 text-sm font-semibold text-ink">
                    <Network className="h-4 w-4" />
                    LLM / API 配置
                  </div>
                  <div className="mt-1 text-xs leading-6 text-ink-faint">
                    在这里配置第三方 OpenAI 兼容接口、模型名称和总代理的开始任务阈值。密钥只会写入本地 `.env`，不会回显已有值。
                  </div>
                </div>
                <div className="rounded-full bg-white px-3 py-1 text-xs text-ink-faint">
                  当前提供商：{llmSettings?.provider ?? '--'}
                </div>
              </div>

              <div className="mt-4 grid gap-4 xl:grid-cols-2">
                <label className="block">
                  <div className="mb-2 text-sm font-medium text-ink">提供商</div>
                  <select
                    value={llmDraft.provider}
                    onChange={(event) => handleLlmDraftChange('provider', event.target.value)}
                    className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-[#bda98b]"
                  >
                    <option value="openai">OpenAI 兼容接口</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="ollama">Ollama</option>
                    <option value="auto">Auto</option>
                  </select>
                </label>

                <label className="block">
                  <div className="mb-2 text-sm font-medium text-ink">模型名称</div>
                  <input
                    value={llmDraft.model}
                    onChange={(event) => handleLlmDraftChange('model', event.target.value)}
                    placeholder="例如：gpt-5.4"
                    className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-[#bda98b]"
                  />
                </label>

                <label className="block xl:col-span-2">
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium text-ink">
                    <Network className="h-4 w-4" />
                    接口地址
                  </div>
                  <input
                    value={llmDraft.base_url}
                    onChange={(event) => handleLlmDraftChange('base_url', event.target.value)}
                    placeholder="例如：https://shiyunapi.com/v1"
                    className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-[#bda98b]"
                  />
                </label>

                <label className="block xl:col-span-2">
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium text-ink">
                    <KeyRound className="h-4 w-4" />
                    API Key
                  </div>
                  <input
                    type="password"
                    value={llmDraft.api_key}
                    onChange={(event) => handleLlmDraftChange('api_key', event.target.value)}
                    placeholder={
                      llmSettings?.api_key_configured
                        ? '已配置密钥，如需更换请重新输入'
                        : '请输入 API Key'
                    }
                    className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-[#bda98b]"
                  />
                </label>

                <label className="block">
                  <div className="mb-2 text-sm font-medium text-ink">超时时间（秒）</div>
                  <input
                    type="number"
                    min={5}
                    max={300}
                    value={llmDraft.timeout_seconds}
                    onChange={(event) =>
                      handleLlmDraftChange('timeout_seconds', Number(event.target.value) || 60)
                    }
                    className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-[#bda98b]"
                  />
                </label>

                <label className="block">
                  <div className="mb-2 flex items-center gap-2 text-sm font-medium text-ink">
                    <ShieldCheck className="h-4 w-4" />
                    总代理开始阈值（%）
                  </div>
                  <input
                    type="number"
                    min={50}
                    max={100}
                    value={llmDraft.manager_readiness_threshold}
                    onChange={(event) =>
                      handleLlmDraftChange(
                        'manager_readiness_threshold',
                        Number(event.target.value) || 85,
                      )
                    }
                    className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-[#bda98b]"
                  />
                </label>
              </div>

              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => {
                    void handleTestLlmSettings()
                  }}
                  disabled={isTestingLlmSettings}
                  className="inline-flex items-center gap-2 rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink transition hover:bg-[#faf7f1] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <WandSparkles className="h-4 w-4" />
                  {isTestingLlmSettings ? '测试中...' : '测试连接'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    void handleSaveLlmSettings()
                  }}
                  disabled={isSavingLlmSettings}
                  className="inline-flex items-center gap-2 rounded-2xl bg-[#1f1c17] px-4 py-3 text-sm text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Save className="h-4 w-4" />
                  {isSavingLlmSettings ? '保存中...' : '保存 API 配置'}
                </button>
              </div>

              {llmTestResult ? (
                <div className="mt-4 rounded-[20px] border border-line bg-white/80 px-4 py-4">
                  <div className="text-sm font-semibold text-ink">连接测试结果</div>
                  <div className="mt-2 text-sm text-ink-soft">
                    运行标签：{llmTestResult.runtime_label}
                  </div>
                  <div className="mt-2 text-sm leading-6 text-ink-soft">
                    返回内容：{llmTestResult.message}
                  </div>
                </div>
              ) : null}
            </div>

            <div className="rounded-[22px] border border-line bg-[#faf7f1] px-4 py-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="text-sm font-semibold text-ink">本地插件</div>
                  <div className="mt-1 text-xs leading-6 text-ink-faint">
                    插件目录位于仓库根目录 `plugins/`。启用后，插件声明的角色模板会在重新规划工作流时按关键词参与选角。
                  </div>
                </div>
                <div className="rounded-full bg-white px-3 py-1 text-xs text-ink-faint">
                  已安装：{plugins.length} · 已启用：{enabledPluginCount}
                </div>
              </div>

              <div className="mt-4 grid gap-3">
                {plugins.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-line bg-white/80 px-4 py-4 text-sm text-ink-soft">
                    当前还没有检测到本地插件。可在 `plugins/` 或 `plugins/examples/` 下新增插件目录。
                  </div>
                ) : (
                  plugins.map((plugin) => (
                    <div
                      key={plugin.plugin_id}
                      className="rounded-2xl border border-line bg-white/80 px-4 py-4"
                    >
                      <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#ece7dc] text-ink">
                              <Package className="h-4 w-4" />
                            </div>
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <div className="text-base font-semibold text-ink">{plugin.name}</div>
                                <span
                                  className={`rounded-full px-2.5 py-1 text-xs ${
                                    plugin.is_enabled
                                      ? 'bg-[#e8f5ee] text-[#1d6b49]'
                                      : 'bg-[#efece4] text-ink-soft'
                                  }`}
                                >
                                  {plugin.is_enabled ? '已启用' : '已停用'}
                                </span>
                                <span className="rounded-full bg-[#eff2fb] px-2.5 py-1 text-xs text-[#4b5d99]">
                                  {plugin.plugin_id}
                                </span>
                              </div>
                              <div className="mt-1 text-xs text-ink-faint">
                                版本 {plugin.version} · {plugin.source_path}
                              </div>
                            </div>
                          </div>

                          <div className="mt-3 text-sm leading-6 text-ink-soft">{plugin.description}</div>
                          <div className="mt-3 flex flex-wrap gap-2 text-xs text-ink-faint">
                            <span className="rounded-full bg-[#f3efe6] px-2.5 py-1">
                              工具：{plugin.tools.join(' / ') || '未声明'}
                            </span>
                            <span className="rounded-full bg-[#f3efe6] px-2.5 py-1">
                              模板：{plugin.agent_templates.length}
                            </span>
                          </div>
                          <div className="mt-3 grid gap-2">
                            {plugin.agent_templates.map((template) => (
                              <div
                                key={template.template_id}
                                className="rounded-2xl border border-line bg-[#faf7f1] px-3 py-3"
                              >
                                <div className="text-sm font-medium text-ink">{template.role_name}</div>
                                <div className="mt-1 text-xs leading-5 text-ink-faint">
                                  {template.summary}
                                </div>
                                <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-ink-faint">
                                  <span className="rounded-full bg-white px-2 py-1">
                                    关键词：{template.trigger_keywords.join(' / ') || '无'}
                                  </span>
                                  <span className="rounded-full bg-white px-2 py-1">
                                    工具：{template.default_tools.join(' / ') || '无'}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => {
                            void handleTogglePlugin(plugin)
                          }}
                          disabled={togglingPluginId === plugin.plugin_id}
                          className="inline-flex items-center justify-center gap-2 rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink transition hover:bg-[#faf7f1] disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          <Power className="h-4 w-4" />
                          {togglingPluginId === plugin.plugin_id
                            ? '保存中...'
                            : plugin.is_enabled
                              ? '停用插件'
                              : '启用插件'}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="text-sm font-semibold text-ink">角色模板导入 / 导出</div>
                <div className="mt-1 text-xs leading-6 text-ink-faint">
                  导出后可在其他账号或环境中导入。导入时支持“跳过同名角色”或“覆盖同名角色”两种策略。
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => {
                    void handleExportTemplates()
                  }}
                  disabled={isExporting}
                  className="inline-flex items-center gap-2 rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink transition hover:bg-[#faf7f1] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Download className="h-4 w-4" />
                  {isExporting ? '导出中...' : '导出模板'}
                </button>
                <button
                  type="button"
                  onClick={handleOpenImportFilePicker}
                  disabled={isImporting}
                  className="inline-flex items-center gap-2 rounded-2xl bg-[#1f1c17] px-4 py-3 text-sm text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <FileUp className="h-4 w-4" />
                  {isImporting ? '导入中...' : '导入模板'}
                </button>
              </div>
            </div>

            <div className="rounded-[22px] border border-line bg-[#faf7f1] px-4 py-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <div className="text-sm font-semibold text-ink">工作流并发上限</div>
                  <div className="mt-1 text-xs leading-6 text-ink-faint">
                    修改 `MAX_CONCURRENT_WORKFLOWS` 后会写回仓库根目录 `.env`，并立即对当前进程生效。
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 text-xs text-ink-faint">
                  <span className="rounded-full bg-white px-3 py-1">
                    当前上限：{runtimeSettings?.max_concurrent_workflows ?? '--'}
                  </span>
                  <span className="rounded-full bg-white px-3 py-1">
                    执行中：{runtimeSettings?.active_workflow_count ?? '--'}
                  </span>
                  <span className="rounded-full bg-white px-3 py-1">
                    剩余槽位：{runtimeSettings?.remaining_slots ?? '--'}
                  </span>
                  <span className="rounded-full bg-white px-3 py-1">
                    状态：{runtimeSettings ? (runtimeSettings.is_limit_reached ? '已满' : '可用') : '--'}
                  </span>
                </div>
              </div>

              <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1fr)_180px]">
                <label className="block">
                  <div className="mb-2 text-xs uppercase tracking-[0.18em] text-ink-faint">
                    新的并发上限
                  </div>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={concurrencyLimitInput}
                    onChange={(event) => setConcurrencyLimitInput(event.target.value)}
                    className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-[#bda98b]"
                  />
                </label>
                <button
                  type="button"
                  onClick={() => {
                    void handleSaveConcurrencyLimit()
                  }}
                  disabled={
                    isSavingConcurrencyLimit ||
                    parsedConcurrencyLimit === null ||
                    runtimeSettings === null ||
                    parsedConcurrencyLimit === runtimeSettings.max_concurrent_workflows
                  }
                  className="inline-flex items-center justify-center rounded-2xl bg-[#1f1c17] px-4 py-3 text-sm text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Save className="mr-2 h-4 w-4" />
                  {isSavingConcurrencyLimit ? '保存中...' : '保存上限'}
                </button>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="text-xs uppercase tracking-[0.18em] text-ink-faint">冲突策略</div>
              <button
                type="button"
                onClick={() => setImportConflictStrategy('skip')}
                className={`rounded-full px-3 py-2 text-xs transition ${
                  importConflictStrategy === 'skip'
                    ? 'bg-[#1f1c17] text-white'
                    : 'border border-line bg-white text-ink-soft'
                }`}
              >
                跳过同名角色
              </button>
              <button
                type="button"
                onClick={() => setImportConflictStrategy('overwrite')}
                className={`rounded-full px-3 py-2 text-xs transition ${
                  importConflictStrategy === 'overwrite'
                    ? 'bg-[#1f1c17] text-white'
                    : 'border border-line bg-white text-ink-soft'
                }`}
              >
                覆盖同名角色
              </button>
            </div>

            {importResult ? (
              <div className="rounded-[22px] border border-line bg-[#faf7f1] px-4 py-4">
                <div className="flex flex-wrap gap-3 text-xs text-ink-faint">
                  <span>总计：{importResult.total_count}</span>
                  <span>新增：{importResult.created_count}</span>
                  <span>覆盖：{importResult.updated_count}</span>
                  <span>跳过：{importResult.skipped_count}</span>
                </div>
                <div className="mt-3 grid gap-2">
                  {importResult.results.map((result) => (
                    <div
                      key={`${result.role_name}-${result.template_id ?? 'none'}-${result.status}`}
                      className="rounded-2xl border border-line bg-white/80 px-3 py-3 text-sm text-ink-soft"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium text-ink">{result.role_name}</span>
                        <span className="rounded-full bg-[#ece7dc] px-2 py-0.5 text-[11px] text-ink-soft">
                          {result.status}
                        </span>
                      </div>
                      <div className="mt-1 text-xs leading-5 text-ink-faint">{result.message}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          {pageError ? (
            <div className="mt-4 rounded-[20px] border border-[#efc1ba] bg-[#fff3f1] px-4 py-3 text-sm text-[#9f3d2e]">
              {pageError}
            </div>
          ) : null}
        </div>

        <div className="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
          <aside className="rounded-[28px] border border-line bg-surface-panel p-6 shadow-panel">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#ece7dc] text-ink">
                {editingTemplateId === null ? <Plus className="h-5 w-5" /> : <PencilLine className="h-5 w-5" />}
              </div>
              <div>
                <div className="text-base font-semibold text-ink">
                  {editingTemplateId === null ? '新建角色模板' : '编辑角色模板'}
                </div>
                <div className="mt-1 text-xs leading-5 text-ink-faint">
                  角色模板会在“重新规划”后参与工作流选角。
                </div>
              </div>
            </div>

            <div className="mt-5 space-y-4">
              <label className="block">
                <div className="mb-2 text-sm font-medium text-ink">角色名称</div>
                <input
                  value={draft.role_name}
                  onChange={(event) => handleDraftChange('role_name', event.target.value)}
                  placeholder="例如：运维工程师"
                  className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-[#bda98b]"
                />
              </label>

              <label className="block">
                <div className="mb-2 text-sm font-medium text-ink">角色摘要</div>
                <input
                  value={draft.summary}
                  onChange={(event) => handleDraftChange('summary', event.target.value)}
                  placeholder="概括这个角色负责的交付范围。"
                  className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-[#bda98b]"
                />
              </label>

              <label className="block">
                <div className="mb-2 text-sm font-medium text-ink">系统提示词</div>
                <textarea
                  value={draft.system_prompt}
                  onChange={(event) => handleDraftChange('system_prompt', event.target.value)}
                  placeholder="描述这个角色的职责、输出风格和关注重点。"
                  rows={6}
                  className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm leading-6 text-ink outline-none transition focus:border-[#bda98b]"
                />
              </label>

              <label className="block">
                <div className="mb-2 text-sm font-medium text-ink">触发关键词</div>
                <textarea
                  value={keywordInput}
                  onChange={(event) => setKeywordInput(event.target.value)}
                  placeholder="可用逗号或换行分隔，例如：运维, 部署, 监控"
                  rows={4}
                  className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm leading-6 text-ink outline-none transition focus:border-[#bda98b]"
                />
              </label>

              <div>
                <div className="mb-2 text-sm font-medium text-ink">可用工具</div>
                <div className="flex flex-wrap gap-2">
                  {supportedTools.map((tool) => {
                    const selected = draft.default_tools.includes(tool.id)
                    return (
                      <button
                        key={tool.id}
                        type="button"
                        onClick={() => handleToggleTool(tool.id)}
                        className={`rounded-full px-3 py-2 text-xs transition ${
                          selected
                            ? 'bg-[#1f1c17] text-white'
                            : 'border border-line bg-white text-ink-soft'
                        }`}
                      >
                        {tool.label}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="grid grid-cols-[1fr_1fr] gap-4">
                <label className="block">
                  <div className="mb-2 text-sm font-medium text-ink">最大重试次数</div>
                  <input
                    type="number"
                    min={0}
                    max={5}
                    value={draft.max_retries}
                    onChange={(event) =>
                      handleDraftChange('max_retries', Number(event.target.value) || 0)
                    }
                    className="w-full rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-[#bda98b]"
                  />
                </label>
                <label className="flex items-center gap-3 rounded-2xl border border-line bg-white px-4 py-3">
                  <input
                    type="checkbox"
                    checked={draft.is_enabled}
                    onChange={(event) => handleDraftChange('is_enabled', event.target.checked)}
                    className="h-4 w-4 rounded border-line"
                  />
                  <span className="text-sm text-ink">启用该角色</span>
                </label>
              </div>
            </div>

            <div className="mt-5 flex gap-3">
              <button
                type="button"
                onClick={() => {
                  void handleSubmit()
                }}
                disabled={isSubmitting}
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-2xl bg-[#1f1c17] px-4 py-3 text-sm text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Save className="h-4 w-4" />
                {isSubmitting ? '保存中...' : editingTemplateId === null ? '创建角色' : '保存修改'}
              </button>
              <button
                type="button"
                onClick={resetDraft}
                className="rounded-2xl border border-line px-4 py-3 text-sm text-ink transition hover:bg-[#faf7f1]"
              >
                重置
              </button>
            </div>
          </aside>

          <section className="space-y-4">
            {isBootstrapping ? (
              <div className="rounded-[24px] border border-line bg-surface-panel px-5 py-4 text-sm text-ink-soft shadow-panel">
                正在加载当前账号的角色模板...
              </div>
            ) : null}

            {templates.length === 0 && !isBootstrapping ? (
              <div className="rounded-[28px] border border-dashed border-line bg-surface-panel px-6 py-10 text-center text-sm text-ink-soft shadow-panel">
                当前还没有自定义角色模板。你可以先创建一个角色，再返回聊天页重新规划工作流。
              </div>
            ) : null}

            {templates.map((template) => (
              <article
                key={template.template_id}
                className="rounded-[28px] border border-line bg-surface-panel p-6 shadow-panel"
              >
                <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#ece7dc] text-ink">
                        <Bot className="h-5 w-5" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="text-xl font-semibold text-ink">{template.role_name}</h2>
                          <span
                            className={`rounded-full px-2.5 py-1 text-xs ${
                              template.is_enabled
                                ? 'bg-[#e8f5ee] text-[#1d6b49]'
                                : 'bg-[#efece4] text-ink-soft'
                            }`}
                          >
                            {template.is_enabled ? '已启用' : '已停用'}
                          </span>
                          <span className="rounded-full bg-[#eff2fb] px-2.5 py-1 text-xs text-[#4b5d99]">
                            {template.template_id}
                          </span>
                        </div>
                        <div className="mt-1 text-xs text-ink-faint">
                          最近更新：{formatUpdatedAt(template.updated_at)}
                        </div>
                      </div>
                    </div>

                    <p className="mt-4 text-sm leading-7 text-ink-soft">{template.summary}</p>

                    <div className="mt-4 rounded-[22px] border border-line bg-white/80 px-4 py-4">
                      <div className="text-xs uppercase tracking-[0.18em] text-ink-faint">系统提示词</div>
                      <div className="mt-3 whitespace-pre-wrap text-sm leading-7 text-ink-soft">
                        {template.system_prompt}
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      {template.trigger_keywords.map((keyword) => (
                        <span
                          key={`${template.template_id}-${keyword}`}
                          className="rounded-full bg-[#ece7dc] px-3 py-1 text-xs text-ink-soft"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2 text-xs text-ink-faint">
                      <span className="rounded-full bg-[#f3efe6] px-2.5 py-1">
                        工具：{template.default_tools.join(' / ')}
                      </span>
                      <span className="rounded-full bg-[#f3efe6] px-2.5 py-1">
                        重试：{template.max_retries} 次
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 xl:w-[280px]">
                    <button
                      type="button"
                      onClick={() => handleStartEditing(template)}
                      className="rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink transition hover:bg-[#faf7f1]"
                    >
                      编辑角色
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        void handleToggleTemplate(template)
                      }}
                      className="inline-flex items-center justify-center gap-2 rounded-2xl border border-line bg-white px-4 py-3 text-sm text-ink transition hover:bg-[#faf7f1]"
                    >
                      <Power className="h-4 w-4" />
                      {template.is_enabled ? '停用角色' : '启用角色'}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        void handleDeleteTemplate(template.template_id)
                      }}
                      disabled={isDeletingTemplateId === template.template_id}
                      className="col-span-2 inline-flex items-center justify-center gap-2 rounded-2xl border border-[#efc1ba] bg-[#fff8f7] px-4 py-3 text-sm text-[#9f3d2e] transition hover:bg-[#fff0ed] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <Trash2 className="h-4 w-4" />
                      {isDeletingTemplateId === template.template_id ? '删除中...' : '删除角色'}
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </section>
        </div>
      </section>
    </main>
  )
}
