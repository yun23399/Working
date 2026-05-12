import { ArrowRight, FolderKanban } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useProjectStore } from '../stores/projectStore'

// 项目页，展示阶段一的最小项目列表和切换入口
export function Projects() {
  const navigate = useNavigate()
  const activeProjectId = useProjectStore((state) => state.activeProjectId)
  const projects = useProjectStore((state) => state.projects)
  const setActiveProjectId = useProjectStore((state) => state.setActiveProjectId)

  return (
    <main className="min-h-screen px-6 py-8">
      <section className="mx-auto w-full max-w-5xl rounded-[28px] border border-line bg-surface-panel p-8 shadow-panel">
        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.24em] text-ink-faint">项目视图</div>
            <h1 className="mt-2 text-3xl font-semibold text-ink">最小项目管理</h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-ink-soft">
              当前阶段先使用本地项目分组管理对话，便于在工作台和历史会话之间快速切换。
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/chat')}
            className="flex items-center gap-2 rounded-2xl border border-line bg-[#1f1c17] px-4 py-3 text-sm text-white transition hover:opacity-90"
          >
            返回工作台
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {projects.map((project) => (
            <button
              key={project.id}
              type="button"
              onClick={() => {
                setActiveProjectId(project.id)
                navigate('/chat')
              }}
              className={`rounded-[24px] border p-5 text-left transition ${
                activeProjectId === project.id
                  ? 'border-line bg-[#f8f5ee] shadow-sm'
                  : 'border-line/60 bg-white hover:border-line hover:bg-[#faf7f1]'
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#ece7dc] text-ink">
                    <FolderKanban className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="text-base font-medium text-ink">{project.name}</div>
                    <div className="mt-1 text-xs text-ink-faint">
                      {activeProjectId === project.id ? '当前选中项目' : '点击切换到该项目'}
                    </div>
                  </div>
                </div>
                <span className="rounded-full bg-[#e9e3d7] px-2.5 py-1 text-xs text-ink-soft">
                  {project.conversationIds.length} 条对话
                </span>
              </div>
              <p className="mt-4 text-sm leading-6 text-ink-soft">{project.summary}</p>
            </button>
          ))}
        </div>
      </section>
    </main>
  )
}
