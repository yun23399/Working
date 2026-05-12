// 用户基础信息类型，和后端认证响应保持一致
export interface User {
  id: number
  username: string
  created_at: string
}

// 登录请求体类型
export interface LoginRequest {
  username: string
  password: string
}

// 注册请求体类型
export interface RegisterRequest {
  username: string
  password: string
}

// 登录响应类型，包含访问令牌与用户信息
export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}
