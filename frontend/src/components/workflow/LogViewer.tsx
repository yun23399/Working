import { useMemo, useState } from 'react'
import { Download, Search } from 'lucide-react'
import type { ActivityLog } from '../../types/chat'
import { downloadBlobFile } from '../../utils/export'

interface LogViewerProps {
  logs: ActivityLog[]
}

const levelOptions: ActivityLog['level'][] = ['DEBUG', 'INFO', 'WARNING', 'ERROR']

// 根据日志等级返回对应的强调色，便于快速区分异常级别
function resolveLevelClassName(level: ActivityLog['level']): string {
  if (level === 'ERROR') {
    return 'text-[#a24545]'
  }

  if (level === 'WARNING') {
    return 'text-[#8a620b]'
  }

  return 'text-[#4263eb]'
}

// 将后端时间戳格式化为日志面板可读时间
function formatLogTimestamp(value: string | undefined): string {
  if (!value) {
    return '--:--'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '--:--'
  }

  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(date)
}

// 工作流日志面板，展示当前执行过程中的结构化实时日志
export function LogViewer({ logs }: LogViewerProps) {
  const [levelFilter, setLevelFilter] = useState<'ALL' | ActivityLog['level']>('ALL')
  const [searchKeyword, setSearchKeyword] = useState('')

  const filteredLogs = useMemo(() => {
    const normalizedKeyword = searchKeyword.trim().toLowerCase()
    return logs.filter((log) => {
      const levelMatched = levelFilter === 'ALL' || log.level === levelFilter
      const keywordMatched =
        normalizedKeyword.length === 0 ||
        `${log.message} ${log.agentId}`.toLowerCase().includes(normalizedKeyword)
      return levelMatched && keywordMatched
    })
  }, [levelFilter, logs, searchKeyword])

  // 导出当前筛选结果，方便离线排查工作流执行过程
  const handleExportLogs = () => {
    const lines = filteredLogs.map(
      (log) =>
        `[${log.level}] ${formatLogTimestamp(log.timestamp)} ${log.agentId} ${log.message}`,
    )
    const fileContent = `${lines.join('\n')}\n`
    downloadBlobFile(
      new Blob([fileContent], { type: 'text/plain;charset=utf-8' }),
      'workflow-runtime-logs.txt',
    )
  }

  return (
    <section className="rounded-[20px] border border-line bg-white/85 px-5 py-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-ink">执行日志</div>
          <div className="mt-1 text-xs text-ink-faint">
            展示当前工作流节点推进中的实时事件，支持分级过滤与关键词筛选。
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-[#f3efe6] px-3 py-1 text-xs text-ink-soft">
            {filteredLogs.length} / {logs.length} 条
          </div>
          <button
            type="button"
            onClick={handleExportLogs}
            disabled={filteredLogs.length === 0}
            className="inline-flex items-center gap-2 rounded-full border border-line bg-white px-3 py-1 text-xs text-ink transition hover:bg-[#faf7f1] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Download className="h-3.5 w-3.5" />
            导出
          </button>
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-3">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setLevelFilter('ALL')}
            className={`rounded-full px-3 py-1 text-xs transition ${
              levelFilter === 'ALL'
                ? 'bg-[#1f1c17] text-white'
                : 'border border-line bg-white text-ink-soft'
            }`}
          >
            全部
          </button>
          {levelOptions.map((level) => (
            <button
              key={level}
              type="button"
              onClick={() => setLevelFilter(level)}
              className={`rounded-full px-3 py-1 text-xs transition ${
                levelFilter === level
                  ? 'bg-[#1f1c17] text-white'
                  : 'border border-line bg-white text-ink-soft'
              }`}
            >
              {level}
            </button>
          ))}
        </div>

        <label className="flex items-center gap-3 rounded-2xl border border-line bg-[#faf7f0] px-4 py-3">
          <Search className="h-4 w-4 text-ink-faint" />
          <input
            value={searchKeyword}
            onChange={(event) => setSearchKeyword(event.target.value)}
            placeholder="搜索日志内容或节点编号"
            className="w-full border-none bg-transparent text-sm text-ink outline-none placeholder:text-ink-faint"
          />
        </label>
      </div>

      {logs.length === 0 ? (
        <div className="mt-4 rounded-[18px] border border-dashed border-line bg-[#faf7f0] px-4 py-4 text-sm text-ink-soft">
          当前还没有工作流实时日志。开始执行后，节点状态、编排器推进和错误信息会显示在这里。
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="mt-4 rounded-[18px] border border-dashed border-line bg-[#faf7f0] px-4 py-4 text-sm text-ink-soft">
          当前筛选条件下没有匹配日志，请调整等级或关键词。
        </div>
      ) : (
        <div className="mt-4 max-h-[280px] space-y-3 overflow-y-auto pr-1 font-mono text-xs">
          {filteredLogs.map((log) => (
            <div
              key={log.id}
              className="rounded-[18px] border border-line bg-[#faf7f0] px-4 py-3"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className={`font-semibold ${resolveLevelClassName(log.level)}`}>
                  [{log.level}]
                </span>
                <span className="rounded-full bg-white px-2 py-1 text-[11px] text-ink-faint">
                  {formatLogTimestamp(log.timestamp)}
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
