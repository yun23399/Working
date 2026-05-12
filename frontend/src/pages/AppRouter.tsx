import { Navigate, Route, Routes } from 'react-router-dom'
import { Chat } from './Chat'
import { Login } from './Login'
import { Projects } from './Projects'
import { Settings } from './Settings'

// 应用路由入口，定义阶段一的页面路由结构
export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/chat" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/chat" element={<Chat />} />
      <Route path="/projects" element={<Projects />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
  )
}
