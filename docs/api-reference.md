# API 接口契约

本文档记录当前仓库已经实现并验证过的核心接口。所有错误返回统一遵守以下格式：

```json
{
  "error": "错误描述",
  "code": "错误码",
  "detail": "详细信息"
}
```

---

## 1. 认证接口

### POST /api/auth/register

用途：注册新用户。

请求体：

```json
{
  "username": "alice",
  "password": "secret123"
}
```

成功响应：

```json
{
  "id": 1,
  "username": "alice",
  "created_at": "2026-05-12T09:00:00Z"
}
```

错误码：

- `USER_ALREADY_EXISTS`
- `VALIDATION_ERROR`
- `REGISTER_FAILED`

### POST /api/auth/login

用途：用户登录并获取 JWT。

请求体：

```json
{
  "username": "alice",
  "password": "secret123"
}
```

成功响应：

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "alice",
    "created_at": "2026-05-12T09:00:00Z"
  }
}
```

错误码：

- `INVALID_CREDENTIALS`
- `VALIDATION_ERROR`
- `LOGIN_FAILED`

### GET /api/auth/me

用途：返回当前登录用户信息。

请求头：

```text
Authorization: Bearer <access_token>
```

成功响应：

```json
{
  "id": 1,
  "username": "alice",
  "created_at": "2026-05-12T09:00:00Z"
}
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`

---

## 2. 对话接口

### GET /api/conversations

用途：获取当前用户的对话列表，按最近更新时间倒序返回。

成功响应：

```json
[
  {
    "id": 2,
    "title": "新对话 05/12 11:46",
    "created_at": "2026-05-12T11:46:00Z",
    "updated_at": "2026-05-12T11:46:12Z"
  }
]
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `LIST_CONVERSATIONS_FAILED`

### POST /api/conversations

用途：创建新对话。

请求体：

```json
{
  "title": "商品页开发"
}
```

成功响应：

```json
{
  "id": 3,
  "title": "商品页开发",
  "created_at": "2026-05-12T11:50:00Z",
  "updated_at": "2026-05-12T11:50:00Z"
}
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `VALIDATION_ERROR`
- `CREATE_CONVERSATION_FAILED`

### GET /api/conversations/{conversation_id}/messages

用途：获取指定对话的历史消息。

成功响应：

```json
[
  {
    "id": 10,
    "conversation_id": 3,
    "role": "user",
    "content": "帮我做一个商品详情页",
    "token_count": 1,
    "created_at": "2026-05-12T11:50:10Z"
  },
  {
    "id": 11,
    "conversation_id": 3,
    "role": "assistant",
    "content": "我已经理解到你要构建一个商品详情页。下一步我会先帮你梳理页面模块、信息结构与关键交互，再继续细化实现范围。",
    "token_count": 32,
    "created_at": "2026-05-12T11:50:11Z"
  }
]
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `CONVERSATION_NOT_FOUND`
- `LIST_MESSAGES_FAILED`

### POST /api/conversations/{conversation_id}/chat

用途：发送用户消息，并触发 Manager Agent 的真实流式回复。

请求体：

```json
{
  "content": "帮我做一个商品详情页"
}
```

成功响应：

```json
{
  "message_id": 12,
  "conversation_id": 3,
  "accepted": true
}
```

说明：

- HTTP 接口负责写入用户消息并启动后台流式任务
- 实际回复内容通过 WebSocket 返回
- 若当前 LLM 配置无效或模型调用失败，错误也会通过 WebSocket `error` 事件返回

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `CONVERSATION_NOT_FOUND`
- `VALIDATION_ERROR`
- `CHAT_REQUEST_FAILED`

---

## 3. WebSocket 接入说明

当前实时端点：

```text
/ws/{conversation_id}?token=<access_token>
```

当前支持两种鉴权方式：

1. 查询参数 `token`
2. `Authorization: Bearer <access_token>` 请求头

当前后端会校验：

1. Token 是否有效
2. 当前用户是否拥有该对话

更多消息体示例见 [`websocket-protocol.md`](./websocket-protocol.md)。

---

## 4. 工作流预览接口

### GET /api/workflows/{conversation_id}

用途：获取指定对话下的工作流预览列表，按最近创建时间倒序返回。

成功响应：

```json
[
  {
    "workflow_id": 4,
    "conversation_id": 11,
    "status": "draft",
    "requirement": {
      "goal": "请先帮我规划一个支持前端页面、文档输出和流程确认的项目，并生成可确认的工作流预览。",
      "constraints": [
        "需围绕当前对话《阶段二预览验证 200436》推进"
      ],
      "output_types": ["code", "document"],
      "context": "请先帮我规划一个支持前端页面、文档输出和流程确认的项目，并生成可确认的工作流预览。"
    },
    "dag": {
      "execution_mode": "serial",
      "nodes": [
        {
          "id": "node_1",
          "role": "需求分析师",
          "task": "梳理目标、约束与交付范围，输出执行摘要。",
          "tools": ["file_tool"],
          "llm": "ollama/qwen2.5-coder:3b",
          "max_retries": 2,
          "depends_on": []
        }
      ]
    },
    "created_at": "2026-05-12T20:04:37Z",
    "updated_at": "2026-05-12T20:04:37Z"
  }
]
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `CONVERSATION_NOT_FOUND`
- `LIST_WORKFLOWS_FAILED`

### POST /api/workflows/{conversation_id}/preview

用途：为指定对话生成工作流预览，或在 `force_replan=true` 时重新规划。

请求体：

```json
{
  "force_replan": false
}
```

成功响应：

```json
{
  "workflow_id": 3,
  "conversation_id": 11,
  "status": "draft",
  "requirement": {
    "goal": "请先帮我规划一个支持前端页面、文档输出和流程确认的项目，并生成可确认的工作流预览。",
    "constraints": [
      "需围绕当前对话《阶段二预览验证 200436》推进",
      "交付内容需兼顾文档表达清晰度",
      "需要体现前端界面或交互实现要求"
    ],
    "output_types": ["code", "document"],
    "context": "请先帮我规划一个支持前端页面、文档输出和流程确认的项目，并生成可确认的工作流预览。"
  },
  "dag": {
    "execution_mode": "serial",
    "nodes": [
      {
        "id": "node_1",
        "role": "需求分析师",
        "task": "梳理目标、约束与交付范围，输出执行摘要。",
        "tools": ["file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 2,
        "depends_on": []
      },
      {
        "id": "node_2",
        "role": "方案规划师",
        "task": "根据需求摘要生成实施方案、任务拆分和风险提示。",
        "tools": ["file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 2,
        "depends_on": ["node_1"]
      },
      {
        "id": "node_3",
        "role": "交付执行者",
        "task": "根据确认后的方案产出最终交付物草稿，并整理交接说明。",
        "tools": ["code_executor", "file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 3,
        "depends_on": ["node_2"]
      }
    ]
  },
  "created_at": "2026-05-12T20:04:37Z",
  "updated_at": "2026-05-12T20:04:37Z"
}
```

说明：

- 当当前对话已有预览且 `force_replan=false` 时，直接返回最新预览
- 当 `force_replan=true` 时，会基于当前对话历史重新创建一条新的预览记录
- 当前阶段只做预览与确认，不触发真实 DAG 执行

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `CONVERSATION_NOT_FOUND`
- `VALIDATION_ERROR`
- `CREATE_WORKFLOW_PREVIEW_FAILED`

### POST /api/workflows/{conversation_id}/{workflow_id}/confirm

用途：确认指定工作流预览，当前阶段仅更新状态为 `confirmed`。

成功响应：

```json
{
  "workflow_id": 3,
  "conversation_id": 11,
  "status": "confirmed",
  "requirement": {
    "goal": "请先帮我规划一个支持前端页面、文档输出和流程确认的项目，并生成可确认的工作流预览。",
    "constraints": [
      "需围绕当前对话《阶段二预览验证 200436》推进"
    ],
    "output_types": ["code", "document"],
    "context": "请先帮我规划一个支持前端页面、文档输出和流程确认的项目，并生成可确认的工作流预览。"
  },
  "dag": {
    "execution_mode": "serial",
    "nodes": []
  },
  "created_at": "2026-05-12T20:04:37Z",
  "updated_at": "2026-05-12T20:04:40Z"
}
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `CONVERSATION_NOT_FOUND`
- `WORKFLOW_NOT_FOUND`
- `CONFIRM_WORKFLOW_FAILED`

---

## 5. 当前未实现但已规划的接口

以下接口仍处于规划阶段，暂未在当前仓库中实现：

- `/api/projects`
- `/api/workflows/{conversation_id}/control`
