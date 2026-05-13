import {
  CirclePause,
  ArrowRight,
  CircleStop,
  Check,
  FileText,
  GitBranch,
  LoaderCircle,
  RefreshCw,
  RotateCcw,
  Sparkles,
} from 'lucide-react'
import type { WorkflowPreview } from '../../types/workflow'

interface WorkflowConfirmProps {
  workflow: WorkflowPreview | null
  hasConversation: boolean
  canGenerate: boolean
  errorMessage: string | null
  isLoading: boolean
  isGenerating: boolean
  isConfirming: boolean
  isExecuting: boolean
  isControlling: boolean
  onGenerate: () => void
  onReplan: () => void
  onConfirm: () => void
  onExecute: () => void
  onPause: () => void
  onResume: () => void
  onAbort: () => void
  onRedirect: () => void
}

const outputTypeLabelMap: Record<string, string> = {
  code: '代码',
  document: '文档',
  image: '图像',
  data: '数据',
}

const templateLabelMap: Record<string, string> = {
  pm: 'PM 模板',
  frontend: '前端模板',
  backend: '后端模板',
  qa: '测试模板',
  designer: '设计模板',
}

// 格式化工作流时间，便于在卡片中展示最近更新时间
function formatWorkflowTime(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

// 将输出物类型转换为更友好的中文标签
function resolveOutputTypeLabel(outputType: string): string {
  return outputTypeLabelMap[outputType] ?? outputType
}

// 将模板编号转换为更友好的中文标签
function resolveTemplateLabel(templateId: string): string {
  return templateLabelMap[templateId] ?? templateId
}

// 根据模板来源渲染更明确的来源标签
function resolveTemplateSourceLabel(templateSource: string): string {
  if (templateSource === 'custom') {
    return '自定义角色'
  }

  if (templateSource === 'plugin') {
    return '插件模板'
  }

  return '内置模板'
}

// 根据工作流状态返回对应的界面提示
function resolveStatusMeta(status: string): {
  label: string
  className: string
} {
  if (status === 'completed') {
    return {
      label: '已完成',
      className: 'bg-[#e8f5ee] text-[#1d6b49]',
    }
  }

  if (status === 'running') {
    return {
      label: '执行中',
      className: 'bg-[#fff4de] text-[#9a6700]',
    }
  }

  if (status === 'failed') {
    return {
      label: '执行失败',
      className: 'bg-[#fff0ef] text-[#a24545]',
    }
  }

  if (status === 'waiting_confirm') {
    return {
      label: '等待确认',
      className: 'bg-[#fef3c7] text-[#9a6700]',
    }
  }

  if (status === 'confirmed') {
    return {
      label: '已确认',
      className: 'bg-[#e8f5ee] text-[#1d6b49]',
    }
  }

  return {
    label: '待确认',
    className: 'bg-[#eff2fb] text-[#4b5d99]',
  }
}

// 生成等待确认状态下的辅助说明，区分普通断点与错误恢复
function resolveWaitingDescription(workflow: WorkflowPreview): string | null {
  if (workflow.status !== 'waiting_confirm') {
    return null
  }

  if (workflow.error_report) {
    return `当前节点 ${workflow.error_report.failed_node_id} 执行失败，已回滚到最近安全快照，等待人工恢复。`
  }

  if (workflow.workflow_run.checkpoint_node_id) {
    return `当前工作流在节点 ${workflow.workflow_run.checkpoint_node_id} 后进入断点等待。`
  }

  return '当前工作流处于等待确认状态。'
}

// 工作流预览确认卡片，只负责展示结构化结果和操作入口
export function WorkflowConfirm({
  workflow,
  hasConversation,
  canGenerate,
  errorMessage,
  isLoading,
  isGenerating,
  isConfirming,
  isExecuting,
  isControlling,
  onGenerate,
  onReplan,
  onConfirm,
  onExecute,
  onPause,
  onResume,
  onAbort,
  onRedirect,
}: WorkflowConfirmProps) {
  const statusMeta = workflow ? resolveStatusMeta(workflow.status) : null
  const waitingDescription = workflow ? resolveWaitingDescription(workflow) : null
  const emptyStateDescription = !hasConversation
    ? '先选择或创建一条对话，再基于当前上下文生成工作流预览。'
    : canGenerate
      ? '当前对话已经具备基础需求内容，可以先生成工作流预览，再决定是否进入后续执行。'
      : '先在当前对话里发送至少一条用户需求，再生成更可靠的工作流预览。'

  return (
    <section className="shrink-0 overflow-hidden rounded-[24px] border border-line bg-[linear-gradient(180deg,rgba(255,255,255,0.95)_0%,rgba(247,243,235,0.96)_100%)] shadow-sm">
      <div className="border-b border-line/80 px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-[#ebe7db] px-3 py-1 text-xs text-ink-soft">
              <GitBranch className="h-3.5 w-3.5" />
              阶段二 · 工作流预览
            </div>
            <h2 className="mt-3 text-xl font-semibold text-ink">先确认执行链路，再进入后续编排</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
              当前版本先提供需求提取、节点拆分、确认和最小串行执行入口。断点、并发和工具编排将在后续步骤补齐。
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {workflow && statusMeta ? (
              <span className={`rounded-full px-3 py-1 text-xs ${statusMeta.className}`}>
                {statusMeta.label}
              </span>
            ) : null}
            {!workflow ? (
              <button
                type="button"
                onClick={onGenerate}
                disabled={!canGenerate || isGenerating}
                className="inline-flex items-center gap-2 rounded-2xl bg-ink px-4 py-3 text-sm text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isGenerating ? (
                  <LoaderCircle className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                生成预览
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={onReplan}
                  disabled={isGenerating || workflow.status === 'running'}
                  className="inline-flex items-center gap-2 rounded-2xl border border-line bg-white/80 px-4 py-3 text-sm text-ink transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isGenerating ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  重新规划
                </button>
                <button
                  type="button"
                  onClick={onConfirm}
                  disabled={workflow.status !== 'draft' || isConfirming}
                  className="inline-flex items-center gap-2 rounded-2xl bg-ink px-4 py-3 text-sm text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isConfirming ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <Check className="h-4 w-4" />
                  )}
                  确认工作流
                </button>
                <button
                  type="button"
                  onClick={onExecute}
                  disabled={
                    !['confirmed', 'waiting_confirm'].includes(workflow.status) ||
                    isExecuting
                  }
                  className="inline-flex items-center gap-2 rounded-2xl bg-[#4c6ef5] px-4 py-3 text-sm text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isExecuting ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <ArrowRight className="h-4 w-4" />
                  )}
                  开始执行
                </button>
                <button
                  type="button"
                  onClick={onPause}
                  disabled={workflow.status !== 'running' || isControlling}
                  className="inline-flex items-center gap-2 rounded-2xl border border-line bg-white/80 px-4 py-3 text-sm text-ink transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isControlling ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <CirclePause className="h-4 w-4" />
                  )}
                  请求暂停
                </button>
                <button
                  type="button"
                  onClick={onResume}
                  disabled={workflow.status !== 'waiting_confirm' || isControlling}
                  className="inline-flex items-center gap-2 rounded-2xl border border-line bg-white/80 px-4 py-3 text-sm text-ink transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isControlling ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <RotateCcw className="h-4 w-4" />
                  )}
                  恢复执行
                </button>
                <button
                  type="button"
                  onClick={onRedirect}
                  disabled={workflow.status !== 'waiting_confirm' || isControlling}
                  className="inline-flex items-center gap-2 rounded-2xl border border-line bg-white/80 px-4 py-3 text-sm text-ink transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isControlling ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  改向继续
                </button>
                <button
                  type="button"
                  onClick={onAbort}
                  disabled={!['running', 'waiting_confirm'].includes(workflow.status) || isControlling}
                  className="inline-flex items-center gap-2 rounded-2xl border border-[#e3c2bf] bg-[#fff5f4] px-4 py-3 text-sm text-[#9b4b46] transition hover:bg-[#fff0ef] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isControlling ? (
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                  ) : (
                    <CircleStop className="h-4 w-4" />
                  )}
                  中断执行
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {errorMessage ? (
        <div className="mx-6 mt-4 rounded-[18px] border border-[#e3c2bf] bg-[#fff5f4] px-4 py-3 text-sm text-[#9b4b46]">
          {errorMessage}
        </div>
      ) : null}

      {!workflow ? (
        <div className="grid gap-4 px-6 py-5 md:grid-cols-[1.3fr_0.7fr]">
          <div className="rounded-[20px] border border-dashed border-line bg-white/70 px-5 py-5">
            <div className="text-sm font-medium text-ink">还没有生成工作流预览</div>
            <p className="mt-3 text-sm leading-6 text-ink-soft">{emptyStateDescription}</p>
          </div>
          <div className="rounded-[20px] border border-line bg-[#faf7f0] px-5 py-5">
            <div className="text-xs uppercase tracking-[0.22em] text-ink-faint">预览内容</div>
            <div className="mt-3 space-y-2 text-sm text-ink-soft">
              <div>1. 提取目标、约束和上下文</div>
              <div>2. 生成最小角色节点与依赖顺序</div>
              <div>3. 由你确认后再进入后续执行阶段</div>
            </div>
            {isLoading ? (
              <div className="mt-4 inline-flex items-center gap-2 text-xs text-ink-faint">
                <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                正在同步当前对话的预览记录...
              </div>
            ) : null}
          </div>
        </div>
      ) : (
        <div className="grid gap-4 px-6 py-5 xl:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-4">
            <div className="rounded-[20px] border border-line bg-white/80 px-5 py-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="inline-flex items-center gap-2 text-sm font-medium text-ink">
                  <FileText className="h-4 w-4" />
                  结构化需求摘要
                </div>
                <div className="text-xs text-ink-faint">
                  最近更新 {formatWorkflowTime(workflow.updated_at)}
                </div>
              </div>
              <div className="mt-4 text-xs uppercase tracking-[0.18em] text-ink-faint">目标</div>
              <div className="mt-2 text-sm leading-7 text-ink">{workflow.requirement.goal}</div>
              <div className="mt-4 text-xs uppercase tracking-[0.18em] text-ink-faint">上下文</div>
              <div className="mt-2 whitespace-pre-wrap text-sm leading-7 text-ink-soft">
                {workflow.requirement.context || '当前预览尚未提取到更多上下文。'}
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {workflow.requirement.output_types.map((outputType) => (
                  <span
                    key={outputType}
                    className="rounded-full bg-[#ece7dc] px-3 py-1 text-xs text-ink-soft"
                  >
                    {resolveOutputTypeLabel(outputType)}
                  </span>
                ))}
              </div>
              <div className="mt-4">
                <div className="text-xs uppercase tracking-[0.18em] text-ink-faint">执行进度</div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-[#ece7dc]">
                  <div
                    className="h-full rounded-full bg-[#4c6ef5] transition-all"
                    style={{ width: `${workflow.progress}%` }}
                  />
                </div>
                <div className="mt-2 text-xs text-ink-faint">{workflow.progress}%</div>
              </div>
              <div className="mt-4 rounded-[18px] border border-line bg-[#faf7f0] px-4 py-3 text-sm text-ink-soft">
                当前工作区：{workflow.workspace.workspace_path}
                <div className="mt-2 text-xs text-ink-faint">
                  断点配置：
                  {workflow.workspace.pause_after_nodes.length > 0
                    ? workflow.workspace.pause_after_nodes.join(', ')
                    : '无'}
                </div>
                <div className="mt-1 text-xs text-ink-faint">
                  运行状态：{workflow.workflow_run.status} / 控制信号：{workflow.workflow_run.control_signal}
                </div>
              </div>
              <div className="mt-4 rounded-[20px] border border-line bg-[#f8f4eb] px-4 py-4">
                <div className="text-xs uppercase tracking-[0.18em] text-ink-faint">项目级记忆</div>
                <div className="mt-3 text-sm leading-6 text-ink-soft">
                  长期目标：{workflow.project_memory.latest_goal || '当前尚未沉淀长期目标。'}
                </div>
                <div className="mt-2 text-xs text-ink-faint">
                  记忆文件：{workflow.project_memory.memory_path}
                </div>
                <div className="mt-2 text-xs text-ink-faint">
                  累计工作流：{workflow.project_memory.workflow_count}
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {workflow.project_memory.key_points.length > 0 ? (
                    workflow.project_memory.key_points.map((item) => (
                      <span
                        key={item}
                        className="rounded-full bg-white/80 px-3 py-1 text-xs text-ink-soft"
                      >
                        {item}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-ink-faint">当前还没有沉淀关键记忆。</span>
                  )}
                </div>
                {workflow.project_memory.latest_error ? (
                  <div className="mt-3 rounded-2xl border border-[#e3c2bf] bg-[#fff5f4] px-3 py-3 text-sm leading-6 text-[#7c3f3a]">
                    最近异常：{workflow.project_memory.latest_error.role} ·{' '}
                    {workflow.project_memory.latest_error.error_message}
                  </div>
                ) : null}
              </div>
              {waitingDescription ? (
                <div className="mt-4 rounded-[18px] border border-[#e5d6a2] bg-[#fff8df] px-4 py-3 text-sm text-[#8a6500]">
                  {waitingDescription}
                </div>
              ) : null}
              {workflow.error_report ? (
                <div className="mt-4 rounded-[20px] border border-[#e3c2bf] bg-[#fff5f4] px-4 py-4">
                  <div className="text-xs uppercase tracking-[0.18em] text-[#9b4b46]">
                    错误恢复建议
                  </div>
                  <div className="mt-3 text-sm leading-6 text-[#7c3f3a]">
                    失败节点：{workflow.error_report.failed_role} · {workflow.error_report.failed_node_id}
                  </div>
                  <div className="mt-2 text-sm leading-6 text-[#7c3f3a]">
                    错误原因：{workflow.error_report.error_message}
                  </div>
                  <div className="mt-2 text-sm leading-6 text-[#7c3f3a]">
                    上级角色：{workflow.error_report.upstream_role}
                  </div>
                  <div className="mt-2 text-sm leading-6 text-[#7c3f3a]">
                    已重试：{workflow.error_report.retry_count} / {workflow.error_report.max_retries}
                  </div>
                  <div className="mt-2 text-sm leading-6 text-[#7c3f3a]">
                    回滚断点：{workflow.error_report.rollback_checkpoint_node_id ?? '初始状态'}，进度{' '}
                    {workflow.error_report.rollback_progress}%
                  </div>
                  <div className="mt-3 rounded-2xl bg-white/80 px-3 py-3 text-sm leading-6 text-ink-soft">
                    {workflow.error_report.recovery_suggestion ?? '当前暂无额外恢复建议。'}
                  </div>
                </div>
              ) : null}
              <div className="mt-4">
                <div className="text-xs uppercase tracking-[0.18em] text-ink-faint">约束</div>
                <div className="mt-2 space-y-2">
                  {workflow.requirement.constraints.map((constraint) => (
                    <div
                      key={constraint}
                      className="rounded-2xl border border-line bg-[#faf7f0] px-4 py-3 text-sm leading-6 text-ink-soft"
                    >
                      {constraint}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-[20px] border border-line bg-[#fbf8f2] px-5 py-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-medium text-ink">节点拆分预览</div>
                <div className="mt-1 text-xs text-ink-faint">
                  执行模式：{workflow.dag.execution_mode === 'serial' ? '串行' : workflow.dag.execution_mode}
                </div>
              </div>
              {isLoading ? (
                <div className="inline-flex items-center gap-2 text-xs text-ink-faint">
                  <LoaderCircle className="h-3.5 w-3.5 animate-spin" />
                  同步中
                </div>
              ) : null}
            </div>
            <div className="mt-4 space-y-3">
              {workflow.dag.nodes.map((node, index) => (
                <div
                  key={node.id}
                  className="rounded-[20px] border border-line bg-white/90 px-4 py-4"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#1f1c17] text-xs text-white">
                      {index + 1}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-medium text-ink">{node.role}</span>
                        <span className="rounded-full bg-[#eff2fb] px-2 py-1 text-[11px] text-[#4b5d99]">
                          {node.id}
                        </span>
                        <span className="rounded-full bg-[#ece7dc] px-2 py-1 text-[11px] text-ink-soft">
                          {node.llm}
                        </span>
                        <span className="rounded-full bg-[#eef5ea] px-2 py-1 text-[11px] text-[#42613b]">
                          {resolveTemplateLabel(node.template_id)}
                        </span>
                        <span
                          className={`rounded-full px-2 py-1 text-[11px] ${
                            node.template_source === 'custom'
                              ? 'bg-[#fff3d9] text-[#9a6700]'
                              : node.template_source === 'plugin'
                                ? 'bg-[#eef3ff] text-[#3856a6]'
                              : 'bg-[#f3efe6] text-ink-soft'
                          }`}
                        >
                          {resolveTemplateSourceLabel(node.template_source)}
                        </span>
                        <span className="rounded-full bg-[#f3efe6] px-2 py-1 text-[11px] text-ink-soft">
                          {node.runtime_status ?? 'waiting'}
                        </span>
                      </div>
                      <div className="mt-2 text-sm leading-6 text-ink-soft">{node.task}</div>
                      <div className="mt-3 flex flex-wrap gap-2 text-xs text-ink-faint">
                        <span className="rounded-full bg-[#f3efe6] px-2.5 py-1">
                          工具：{node.tools.join(' / ')}
                        </span>
                        <span className="rounded-full bg-[#f3efe6] px-2.5 py-1">
                          重试：{node.max_retries} 次
                        </span>
                        <span className="rounded-full bg-[#f3efe6] px-2.5 py-1">
                          依赖：{node.depends_on.length > 0 ? node.depends_on.join(', ') : '无'}
                        </span>
                        {node.trigger_keywords.length > 0 ? (
                          <span className="rounded-full bg-[#f3efe6] px-2.5 py-1">
                            关键词：{node.trigger_keywords.join(' / ')}
                          </span>
                        ) : null}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {workflow.execution_logs.length > 0 ? (
              <div className="mt-5 border-t border-line pt-4">
                <div className="text-sm font-medium text-ink">节点交接摘要</div>
                <div className="mt-3 space-y-3">
                  {workflow.execution_logs.map((log) => (
                    <div
                      key={log.node_id}
                      className="rounded-[18px] border border-line bg-white/90 px-4 py-3"
                    >
                      <div className="text-xs text-ink-faint">
                        {log.role} · {log.node_id}
                      </div>
                      <div className="mt-2 text-sm leading-6 text-ink-soft">{log.summary}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </section>
  )
}
