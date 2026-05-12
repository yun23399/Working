import { requestJson } from './client'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from '../types/auth'

// 调用注册接口，创建新账号
export async function registerUser(payload: RegisterRequest): Promise<User> {
  return requestJson<User>('/api/auth/register', {
    method: 'POST',
    body: payload,
  })
}

// 调用登录接口，获取访问令牌与用户信息
export async function loginUser(payload: LoginRequest): Promise<TokenResponse> {
  return requestJson<TokenResponse>('/api/auth/login', {
    method: 'POST',
    body: payload,
  })
}

// 拉取当前登录用户信息，校验本地会话是否有效
export async function fetchCurrentUser(token: string): Promise<User> {
  return requestJson<User>('/api/auth/me', {
    token,
  })
}
