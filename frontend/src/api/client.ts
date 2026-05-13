interface ApiErrorDetail {
  error: string
  code: string
  detail: string
}

interface ApiErrorResponse {
  error?: unknown
  code?: unknown
  detail?: unknown
}

interface RequestJsonOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  token?: string | null
  body?: object
  accept?: string
}

// 统一的 API 请求错误，暴露状态码和后端错误码
export class ApiRequestError extends Error {
  code: string
  status: number

  constructor(message: string, code: string, status: number) {
    super(message)
    this.name = 'ApiRequestError'
    this.code = code
    this.status = status
  }
}

const fallbackApiBaseUrl = 'http://127.0.0.1:8000'

function resolveApiBaseUrl(): string {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined
  return (configuredBaseUrl ?? fallbackApiBaseUrl).replace(/\/$/, '')
}

function isApiErrorDetail(value: unknown): value is ApiErrorDetail {
  if (typeof value !== 'object' || value === null) {
    return false
  }

  const candidate = value as Partial<ApiErrorDetail>
  return (
    typeof candidate.error === 'string' &&
    typeof candidate.code === 'string' &&
    typeof candidate.detail === 'string'
  )
}

function extractApiError(errorBody: ApiErrorResponse, status: number): ApiRequestError {
  if (isApiErrorDetail(errorBody)) {
    return new ApiRequestError(errorBody.error, errorBody.code, status)
  }

  if (isApiErrorDetail(errorBody.detail)) {
    return new ApiRequestError(errorBody.detail.error, errorBody.detail.code, status)
  }

  return new ApiRequestError('请求失败，请稍后重试', 'REQUEST_FAILED', status)
}

// 构造完整的 HTTP 地址，供所有请求统一使用
function buildHttpUrl(path: string): string {
  return `${resolveApiBaseUrl()}${path}`
}

// 统一发送原始 HTTP 请求，并保留响应体供不同类型解析
async function requestResponse(path: string, options: RequestJsonOptions = {}): Promise<Response> {
  const headers = new Headers({
    Accept: options.accept ?? 'application/json',
  })

  if (options.body) {
    headers.set('Content-Type', 'application/json')
  }

  if (options.token) {
    headers.set('Authorization', `Bearer ${options.token}`)
  }

  let response: Response
  try {
    response = await fetch(buildHttpUrl(path), {
      method: options.method ?? 'GET',
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    })
  } catch {
    throw new ApiRequestError('网络连接失败，请确认后端服务已启动', 'NETWORK_ERROR', 0)
  }

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({ detail: undefined }))) as ApiErrorResponse
    throw extractApiError(errorBody, response.status)
  }

  return response
}

// 统一发送 JSON 请求，并将后端错误转换为可处理异常
export async function requestJson<T>(path: string, options: RequestJsonOptions = {}): Promise<T> {
  const response = await requestResponse(path, {
    ...options,
    accept: 'application/json',
  })
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

// 统一读取文本型响应，供代码和文档预览直接消费
export async function requestText(path: string, options: RequestJsonOptions = {}): Promise<string> {
  const response = await requestResponse(path, {
    ...options,
    accept: 'text/plain, application/json;q=0.9, */*;q=0.8',
  })
  return response.text()
}

// 统一读取二进制响应，供图片等产物生成本地预览 URL
export async function requestBlob(path: string, options: RequestJsonOptions = {}): Promise<Blob> {
  const response = await requestResponse(path, {
    ...options,
    accept: '*/*',
  })
  return response.blob()
}

// 根据当前 API 地址推导 WebSocket 地址，避免重复配置
export function buildConversationWebSocketUrl(conversationId: number, token: string): string {
  const apiUrl = new URL(resolveApiBaseUrl())
  apiUrl.protocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:'
  apiUrl.pathname = `/ws/${conversationId}`
  apiUrl.search = new URLSearchParams({ token }).toString()
  return apiUrl.toString()
}
