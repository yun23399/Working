import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogIn, UserPlus } from 'lucide-react'
import { loginUser, registerUser } from '../api/auth'
import { ApiRequestError } from '../api/client'
import { useAuthStore } from '../stores/authStore'

type AuthMode = 'login' | 'register'

interface Credentials {
  username: string
  password: string
}

function resolveAuthError(error: unknown): string {
  if (error instanceof ApiRequestError) {
    return error.message
  }

  return '认证请求失败，请稍后重试'
}

// 登录页面，负责注册、登录和本地会话建立
export function Login() {
  const navigate = useNavigate()
  const token = useAuthStore((state) => state.token)
  const setAuthError = useAuthStore((state) => state.setAuthError)
  const setSession = useAuthStore((state) => state.setSession)
  const authError = useAuthStore((state) => state.authError)
  const [mode, setMode] = useState<AuthMode>('login')
  const [credentials, setCredentials] = useState<Credentials>({
    username: '',
    password: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (token) {
      navigate('/chat', { replace: true })
    }
  }, [navigate, token])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setAuthError(null)
    setIsSubmitting(true)

    try {
      if (mode === 'register') {
        await registerUser(credentials)
      }

      const session = await loginUser(credentials)
      setSession(session.access_token, session.user)
      navigate('/chat', { replace: true })
    } catch (error) {
      setAuthError(resolveAuthError(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(95,124,255,0.16),transparent_24%),linear-gradient(135deg,#f9f7f2_0%,#efe8dd_100%)] px-6 py-10">
      <section className="mx-auto grid min-h-[760px] max-w-6xl overflow-hidden rounded-[32px] border border-line bg-[rgba(255,253,249,0.9)] shadow-panel backdrop-blur md:grid-cols-[1.1fr_0.9fr]">
        <div className="relative overflow-hidden border-b border-line bg-[#f2ecdf] px-8 py-10 md:border-b-0 md:border-r md:px-12 md:py-14">
          <div className="absolute inset-x-0 top-0 h-40 bg-[radial-gradient(circle_at_top,rgba(95,124,255,0.18),transparent_55%)]" />
          <div className="relative max-w-xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#d7cfbf] bg-white/80 px-4 py-2 text-sm text-ink-soft">
              <span className="h-2.5 w-2.5 rounded-full bg-accent" />
              AgentFlow · 阶段一最小闭环
            </div>
            <h1 className="mt-8 text-4xl font-semibold leading-tight text-ink md:text-5xl">
              用真实账号、真实会话、真实 WebSocket
              <span className="block text-[#5c5648]">把多智能体项目先跑通。</span>
            </h1>
            <p className="mt-6 max-w-lg text-base leading-8 text-ink-soft">
              当前页面已接入注册、登录和本地会话持久化。登录后会直接进入聊天主界面，继续验证对话创建、消息发送和流式回复链路。
            </p>
            <div className="mt-10 grid gap-4 md:grid-cols-2">
              <article className="rounded-[24px] border border-[#d8d0c1] bg-white/80 p-5">
                <div className="text-sm font-medium text-ink">认证闭环</div>
                <p className="mt-3 text-sm leading-7 text-ink-soft">
                  支持注册后立即登录，令牌和用户信息会写入本地存储，刷新页面后仍可恢复会话。
                </p>
              </article>
              <article className="rounded-[24px] border border-[#d8d0c1] bg-white/80 p-5">
                <div className="text-sm font-medium text-ink">聊天闭环</div>
                <p className="mt-3 text-sm leading-7 text-ink-soft">
                  进入聊天页后会自动创建或加载对话，并建立受鉴权保护的实时连接，准备接收 Manager 流式输出。
                </p>
              </article>
            </div>
          </div>
        </div>

        <div className="flex items-center px-6 py-8 md:px-10 md:py-12">
          <div className="mx-auto w-full max-w-md">
            <div className="flex rounded-full border border-line bg-[#f2ede3] p-1">
              <button
                type="button"
                onClick={() => {
                  setMode('login')
                  setAuthError(null)
                }}
                className={`flex-1 rounded-full px-4 py-3 text-sm transition ${
                  mode === 'login' ? 'bg-white text-ink shadow-sm' : 'text-ink-soft'
                }`}
              >
                登录
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode('register')
                  setAuthError(null)
                }}
                className={`flex-1 rounded-full px-4 py-3 text-sm transition ${
                  mode === 'register' ? 'bg-white text-ink shadow-sm' : 'text-ink-soft'
                }`}
              >
                注册
              </button>
            </div>

            <div className="mt-8">
              <h2 className="text-3xl font-semibold text-ink">
                {mode === 'login' ? '继续当前项目' : '创建新账号'}
              </h2>
              <p className="mt-3 text-sm leading-7 text-ink-soft">
                {mode === 'login'
                  ? '输入现有账号后进入聊天页。'
                  : '注册完成后系统会自动为你登录并跳转到聊天页。'}
              </p>
            </div>

            {authError ? (
              <div className="mt-6 rounded-[20px] border border-[#e2b9b9] bg-[#fff3f2] px-4 py-3 text-sm text-[#9a3c3c]">
                {authError}
              </div>
            ) : null}

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <label className="block">
                <span className="mb-2 block text-sm text-ink-soft">用户名</span>
                <input
                  value={credentials.username}
                  onChange={(event) =>
                    setCredentials((current) => ({
                      ...current,
                      username: event.target.value,
                    }))
                  }
                  className="w-full rounded-[20px] border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-accent"
                  placeholder="请输入用户名"
                  minLength={3}
                  maxLength={50}
                  required
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm text-ink-soft">密码</span>
                <input
                  type="password"
                  value={credentials.password}
                  onChange={(event) =>
                    setCredentials((current) => ({
                      ...current,
                      password: event.target.value,
                    }))
                  }
                  className="w-full rounded-[20px] border border-line bg-white px-4 py-3 text-sm text-ink outline-none transition focus:border-accent"
                  placeholder="请输入密码"
                  minLength={6}
                  maxLength={128}
                  required
                />
              </label>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex w-full items-center justify-center gap-2 rounded-[20px] bg-ink px-4 py-4 text-sm text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {mode === 'login' ? <LogIn className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />}
                {isSubmitting ? '提交中...' : mode === 'login' ? '登录并进入聊天' : '注册并进入聊天'}
              </button>
            </form>
          </div>
        </div>
      </section>
    </main>
  )
}
