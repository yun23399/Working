# WebSocket 协议文档

WebSocket 端点：

```text
/ws/{conversation_id}
```

连接要求：

- 连接前用户必须已登录
- 连接时必须携带合法 JWT
- 一个 `conversation_id` 可存在多个监听连接

## 消息总结构

```json
{
  "type": "token | agent_status | log | artifact | workflow_update | error",
  "conversation_id": "string",
  "payload": {},
  "timestamp": "ISO8601"
}
```

## 1. token

用途：流式返回文本 token。

```json
{
  "type": "token",
  "conversation_id": "conversation_1",
  "payload": {
    "content": "你好",
    "agent_id": "manager"
  },
  "timestamp": "2026-05-12T09:00:00Z"
}
```

前端行为：

- 将 `content` 追加到当前流式消息
- 若当前没有活跃 Agent 消息，先创建占位消息

## 2. agent_status

用途：推送 Agent 状态变化。

```json
{
  "type": "agent_status",
  "conversation_id": "conversation_1",
  "payload": {
    "agent_id": "manager",
    "status": "running",
    "role": "manager"
  },
  "timestamp": "2026-05-12T09:00:01Z"
}
```

状态枚举：

- `waiting`
- `running`
- `done`
- `failed`

## 3. log

用途：推送执行日志。

```json
{
  "type": "log",
  "conversation_id": "conversation_1",
  "payload": {
    "level": "INFO",
    "message": "正在初始化工作流",
    "agent_id": "manager"
  },
  "timestamp": "2026-05-12T09:00:02Z"
}
```

## 4. artifact

用途：推送产出物。

```json
{
  "type": "artifact",
  "conversation_id": "conversation_1",
  "payload": {
    "type": "code",
    "name": "ProductDetail.tsx",
    "path": "workspace/projects/project_1/ProductDetail.tsx"
  },
  "timestamp": "2026-05-12T09:00:03Z"
}
```

## 5. workflow_update

用途：推送工作流节点状态。

```json
{
  "type": "workflow_update",
  "conversation_id": "conversation_1",
  "payload": {
    "node_id": "node_1",
    "status": "running",
    "progress": 0.3
  },
  "timestamp": "2026-05-12T09:00:04Z"
}
```

## 6. error

用途：推送可恢复或不可恢复错误。

```json
{
  "type": "error",
  "conversation_id": "conversation_1",
  "payload": {
    "message": "模型调用失败",
    "recoverable": true
  },
  "timestamp": "2026-05-12T09:00:05Z"
}
```

## 前端连接策略

- 初次连接失败时提示用户
- 断线后自动重连，最多 3 次
- 重连期间保留现有消息，不清空 UI
- 若重连失败，显示用户可见错误提示

## 阶段一建议实现

阶段一可先使用“模拟流式输出”：

1. HTTP 接口写入用户消息
2. 后端通过 WebSocket 分批推送 `token`
3. 前端展示打字机效果
4. 推送完成后将完整消息写入数据库
