import { AnimatePresence } from 'framer-motion'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { PageTransition } from '../components/layout/PageTransition'
import { useAuthStore } from '../stores/authStore'
import { Chat } from './Chat'
import { Login } from './Login'
import { Projects } from './Projects'
import { Settings } from './Settings'

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const token = useAuthStore((state) => state.token)
  return token ? children : <Navigate to="/login" replace />
}

// 包装页面组件，统一接入页面级转场效果
function withPageTransition(children: JSX.Element): JSX.Element {
  return <PageTransition>{children}</PageTransition>
}

// 应用路由入口，按登录态切换公开页与受保护页面
export function AppRouter() {
  const token = useAuthStore((state) => state.token)
  const location = useLocation()

  return (
    <AnimatePresence mode="wait" initial={false}>
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Navigate to={token ? '/chat' : '/login'} replace />} />
        <Route path="/login" element={withPageTransition(<Login />)} />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              {withPageTransition(<Chat />)}
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects"
          element={
            <ProtectedRoute>
              {withPageTransition(<Projects />)}
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              {withPageTransition(<Settings />)}
            </ProtectedRoute>
          }
        />
      </Routes>
    </AnimatePresence>
  )
}
