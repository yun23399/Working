# API 接口契约

本文档定义阶段一与阶段二会用到的核心接口契约。所有错误返回统一遵守以下格式：

```json
{
  "error": "错误描述",
  "code": "错误码",
  "detail": "详细信息"
}
```

## 1. 认证接口

### POST /api/auth/register

用途：注册新用户。

请求体：

```json
{
  "username": "alice",
  "password": "strong-password"
}
```

成功响应：

```json
{
  "id": "user_123",
  "username": "alice",
  "created_at": "2026-05-12T09:00:00Z"
}
```

错误码：

- `USER_ALREADY_EXISTS`
- `VALIDATION_ERROR`

### POST /api/auth/login

用途：用户登录并获取 JWT。

请求体：

```json
{
  "username": "alice",
  "password": "strong-password"
}
```

成功响应：

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": "user_123",
    "username": "alice"
  }
}
```

错误码：

- `INVALID_CREDENTIALS`
- `VALIDATION_ERROR`

## 2. 项目接口

### GET /api/projects

用途：获取当前用户的项目列表。

成功响应：

```json
[
  {
    "id": "project_1",
    "name": "电商网站项目",
    "description": "商品详情页需求",
    "created_at": "2026-05-12T09:00:00Z",
    "updated_at": "2026-05-12T09:10:00Z"
  }
]
```

### POST /api/projects

用途：创建项目。

请求体：

```json
{
  "name": "电商网站项目",
  "description": "商品详情页需求"
}
```

成功响应：

```json
{
  "id": "project_1",
  "name": "电商网站项目",
  "description": "商品详情页需求"
}
```

## 3. 对话接口

### GET /api/conversations?project_id={project_id}

用途：获取指定项目下的对话列表。

### POST /api/conversations

用途：创建对话。

请求体：

```json
{
  "project_id": "project_1",
  "title": "商品页开发"
}
```

成功响应：

```json
{
  "id": "conversation_1",
  "project_id": "project_1",
  "title": "商品页开发"
}
```

### GET /api/conversations/{conversation_id}/messages

用途：获取历史消息。

成功响应：

```json
[
  {
    "id": "message_1",
    "role": "user",
    "content": "帮我做一个商品详情页",
    "token_count": 12,
    "created_at": "2026-05-12T09:00:00Z"
  }
]
```

### POST /api/conversations/{conversation_id}/chat

用途：发送用户消息，并驱动 Manager Agent 回复。

请求体：

```json
{
  "content": "帮我做一个商品详情页"
}
```

成功响应：

```json
{
  "message_id": "message_2",
  "conversation_id": "conversation_1",
  "accepted": true
}
```

说明：

- 实际回复内容通过 WebSocket 流式返回
- HTTP 接口只负责接收请求并启动处理流程

## 4. 工作流接口

### GET /api/workflows/{conversation_id}

用途：获取当前对话关联的工作流定义。

### POST /api/workflows/{conversation_id}/confirm

用途：用户确认执行工作流。

请求体：

```json
{
  "action": "confirm"
}
```

### POST /api/workflows/{conversation_id}/control

用途：控制工作流暂停、恢复、中止、重定向。

请求体：

```json
{
  "action": "pause | resume | abort | redirect",
  "payload": {}
}
```

## 5. 鉴权说明

- 除 `/api/auth/register` 和 `/api/auth/login` 外，其余接口默认要求 Bearer Token
- 请求头格式：

```text
Authorization: Bearer <access_token>
```
