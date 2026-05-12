import type { ActivityLog } from '../../types/chat'

interface LogViewerProps {
  logs: ActivityLog[]
}

function resolveLevelClassName(level: ActivityLog['level']): string {
  if (level === 'ERROR') {
    return 'text-[#a24545]'
  }

  if (level === 'WARNING') {
    return 'text-[#8a620b]'
  }

  return 'text-[#4263eb]'
}

// 工作流日志面板，展示当前执行过程中的结构化实时日志
export function LogViewer({ logs }: LogViewerProps) {
  return (
    <section className="rounded-[20px] border border-line bg-white/85 px-5 py-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-ink">执行日志</div>
          <div className="mt-1 text-xs text-ink-faint">展示当前工作流节点推进中的实时事件。</div>
        </div>
        <div className="rounded-full bg-[#f3efe6] px-3 py-1 text-xs text-ink-soft">
          {logs.length} 条
        </div>
      </div>

      {logs.length === 0 ? (
        <div className="mt-4 rounded-[18px] border border-dashed border-line bg-[#faf7f0] px-4 py-4 text-sm text-ink-soft">
          当前还没有工作流实时日志。开始执行后，节点状态、编排器推进和错误信息会显示在这里。
        </div>
      ) : (
        <div className="mt-4 max-h-[280px] space-y-3 overflow-y-auto pr-1 font-mono text-xs">
          {logs.map((log) => (
            <div
              key={log.id}
              className="rounded-[18px] border border-line bg-[#faf7f0] px-4 py-3"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className={`font-semibold ${resolveLevelClassName(log.level)}`}>
                  [{log.level}]
                </span>
                <span className="rounded-full bg-white px-2 py-1 text-[11px] text-ink-soft">
                  {log.agentId}
                </span>
              </div>
              <div className="mt-2 whitespace-pre-wrap leading-6 text-ink-soft">
                {log.message}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
