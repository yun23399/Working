import { Navigate, Route, Routes } from 'react-router-dom'
import { Chat } from './Chat'
import { Login } from './Login'
import { Projects } from './Projects'
import { Settings } from './Settings'
import { useAuthStore } from '../stores/authStore'

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const token = useAuthStore((state) => state.token)
  return token ? children : <Navigate to="/login" replace />
}

// 应用路由入口，按登录态切换公开页与受保护页面
export function AppRouter() {
  const token = useAuthStore((state) => state.token)

  return (
    <Routes>
      <Route path="/" element={<Navigate to={token ? '/chat' : '/login'} replace />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        }
      />
      <Route
        path="/projects"
        element={
          <ProtectedRoute>
            <Projects />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
