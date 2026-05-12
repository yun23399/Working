# WebSocket 协议文档

本文档描述当前阶段一已经实现的实时通信协议。

## 1. 端点

```text
/ws/{conversation_id}
```

## 2. 连接要求

- 连接前用户必须已登录
- 必须携带合法 JWT
- 必须拥有目标 `conversation_id` 的访问权限
- 一个 `conversation_id` 可同时存在多个监听连接

当前支持两种鉴权方式：

1. 查询参数：`/ws/{conversation_id}?token=<access_token>`
2. 请求头：`Authorization: Bearer <access_token>`

鉴权失败返回：

- `4401`：Token 缺失或无效
- `4403`：当前用户无权访问该对话

## 3. 消息总结构

```json
{
  "type": "token | agent_status | log | artifact | workflow_update | error",
  "conversation_id": "string",
  "payload": {},
  "timestamp": "ISO8601"
}
```

说明：

- 当前实现中 `conversation_id` 为数字 ID 的字符串形式，例如 `"3"`
- `timestamp` 使用 UTC ISO8601 时间

## 4. token

用途：流式返回回复文本片段。

```json
{
  "type": "token",
  "conversation_id": "3",
  "payload": {
    "content": "需求已收到。",
    "agent_id": "manager"
  },
  "timestamp": "2026-05-12T11:50:10Z"
}
```

前端行为：

- 将 `content` 追加到当前 assistant 流式消息
- 若当前没有活跃流式消息，先创建占位消息

## 5. agent_status

用途：推送 Agent 状态变化。

```json
{
  "type": "agent_status",
  "conversation_id": "3",
  "payload": {
    "agent_id": "manager",
    "status": "running",
    "role": "manager"
  },
  "timestamp": "2026-05-12T11:50:10Z"
}
```

状态枚举：

- `waiting`
- `running`
- `done`
- `failed`

## 6. log

用途：推送执行日志。

```json
{
  "type": "log",
  "conversation_id": "3",
  "payload": {
    "level": "INFO",
    "message": "Manager 正在生成模拟流式回复",
    "agent_id": "manager"
  },
  "timestamp": "2026-05-12T11:50:10Z"
}
```

## 7. error

用途：推送可恢复或不可恢复错误。

```json
{
  "type": "error",
  "conversation_id": "3",
  "payload": {
    "message": "模型调用失败",
    "recoverable": true
  },
  "timestamp": "2026-05-12T11:50:10Z"
}
```

## 8. 当前前端连接策略

- 初次连接时显示连接状态
- 断线后自动重连，最多 3 次
- 重连期间保留消息列表和日志列表
- 重连失败后显示用户可见错误提示
- 当前前端会定时发送 `ping` 文本用于维持连接

## 9. 阶段一当前实现

当前阶段一已经完成以下闭环：

1. HTTP 接口写入用户消息
2. 后端通过 WebSocket 推送 `log`
3. 后端推送 `agent_status=running`
4. 后端分段推送 `token`
5. 后端推送 `agent_status=done`
6. 完整 assistant 消息最终持久化到数据库
