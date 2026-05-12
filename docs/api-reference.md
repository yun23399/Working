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
    "progress": 0,
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
          "template_id": "pm",
          "role": "需求分析师",
          "task": "梳理目标、约束与交付范围，输出执行摘要。",
          "tools": ["file_tool"],
          "llm": "ollama/qwen2.5-coder:3b",
          "max_retries": 2,
          "depends_on": [],
          "runtime_status": "waiting"
        }
      ]
    },
    "execution_logs": [],
    "workspace": {
      "workspace_path": "D:\\AI\\0000001-1\\workspace\\projects\\conversation_11\\workflow_4",
      "status": "draft",
      "progress": 0,
      "active_node_id": null,
      "artifacts": [],
      "updated_at": "2026-05-13T02:10:00+00:00",
      "pause_after_nodes": []
    },
    "project_memory": {
      "memory_path": "D:\\AI\\0000001-1\\workspace\\projects\\conversation_11\\project_memory.json",
      "latest_goal": "请先帮我规划一个支持前端页面、文档输出和流程确认的项目，并生成可确认的工作流预览。",
      "active_constraints": ["需围绕当前对话《阶段二预览验证 200436》推进"],
      "key_points": [
        "请先帮我规划一个支持前端页面、文档输出和流程确认的项目，并生成可确认的工作流预览。"
      ],
      "artifacts": [],
      "workflow_count": 1,
      "latest_error": null,
      "updated_at": "2026-05-13T02:10:00+00:00"
    },
    "handoff_logs": [],
    "workflow_run": {
      "run_id": null,
      "status": "idle",
      "control_signal": "none",
      "checkpoint_node_id": null,
      "redirect_instruction": "",
      "saved_at": null
    },
    "error_report": null,
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
  "force_replan": false,
  "pause_after_nodes": ["node_1"]
}
```

成功响应：

```json
{
  "workflow_id": 3,
  "conversation_id": 11,
  "status": "draft",
  "progress": 0,
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
        "template_id": "pm",
        "role": "需求分析师",
        "task": "梳理目标、约束与交付范围，输出执行摘要。",
        "tools": ["file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 2,
        "depends_on": [],
        "runtime_status": "waiting"
      },
      {
        "id": "node_2",
        "template_id": "frontend",
        "role": "方案规划师",
        "task": "根据需求摘要生成实施方案、任务拆分和风险提示。",
        "tools": ["file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 2,
        "depends_on": ["node_1"],
        "runtime_status": "waiting"
      },
      {
        "id": "node_3",
        "template_id": "backend",
        "role": "交付执行者",
        "task": "根据确认后的方案产出最终交付物草稿，并整理交接说明。",
        "tools": ["code_executor", "file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 3,
        "depends_on": ["node_2"],
        "runtime_status": "waiting"
      }
    ]
  },
  "execution_logs": [],
    "workspace": {
      "workspace_path": "D:\\AI\\0000001-1\\workspace\\projects\\conversation_11\\workflow_3",
      "status": "draft",
      "progress": 0,
      "active_node_id": null,
      "artifacts": [],
      "updated_at": "2026-05-13T02:10:00+00:00",
      "pause_after_nodes": ["node_1"]
    },
    "handoff_logs": [],
    "workflow_run": {
      "run_id": null,
      "status": "idle",
      "control_signal": "none",
      "checkpoint_node_id": null,
      "redirect_instruction": "",
      "saved_at": null
    },
    "error_report": null,
  "created_at": "2026-05-12T20:04:37Z",
  "updated_at": "2026-05-12T20:04:37Z"
}
```

说明：

- 当当前对话已有预览且 `force_replan=false` 时，直接返回最新预览
- 当 `force_replan=true` 时，会基于当前对话历史重新创建一条新的预览记录
- `pause_after_nodes` 可指定断点节点列表，命中后工作流会在节点完成后进入 `waiting_confirm`
- 当前阶段会返回 `progress`、`execution_logs` 和节点 `runtime_status`
- 节点同时返回 `template_id`，用于标识当前角色使用的预置模板
- 当前阶段会同时返回共享工作区 `workspace` 状态和节点交接记录 `handoff_logs`
- 当前阶段会返回 `project_memory`，用于展示同一对话下跨工作流复用的长期上下文
- 当前阶段会返回 `workflow_run`，用于展示运行轮次与断点状态
- 当工作流因节点失败进入人工恢复阶段时，会额外返回 `error_report`
- 预览阶段默认所有节点为 `waiting`

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
  "progress": 0,
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
        "template_id": "pm",
        "role": "需求分析师",
        "task": "梳理目标、约束与交付范围，输出执行摘要。",
        "tools": ["file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 2,
        "depends_on": [],
        "runtime_status": "waiting"
      }
    ]
  },
  "execution_logs": [],
    "workspace": {
      "workspace_path": "D:\\AI\\0000001-1\\workspace\\projects\\conversation_11\\workflow_3",
      "status": "confirmed",
      "progress": 0,
      "active_node_id": null,
      "artifacts": [],
      "updated_at": "2026-05-13T02:10:05+00:00",
      "pause_after_nodes": ["node_1"]
    },
    "handoff_logs": [],
    "workflow_run": {
      "run_id": null,
      "status": "idle",
      "control_signal": "none",
      "checkpoint_node_id": null,
      "redirect_instruction": "",
      "saved_at": null
    },
    "error_report": null,
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

### POST /api/workflows/{conversation_id}/{workflow_id}/execute

用途：启动已确认工作流的最小串行执行链路。

成功响应：

```json
{
  "workflow_id": 7,
  "conversation_id": 16,
  "status": "running",
  "progress": 0,
  "requirement": {
    "goal": "请规划一个需要前端页面、文档和确认流程的项目。",
    "constraints": [
      "需围绕当前对话《阶段二执行验证 231339》推进"
    ],
    "output_types": ["code", "document"],
    "context": "请规划一个需要前端页面、文档和确认流程的项目。"
  },
  "dag": {
    "execution_mode": "serial",
    "nodes": [
      {
        "id": "node_1",
        "template_id": "pm",
        "role": "需求分析师",
        "task": "梳理目标、约束与交付范围，输出执行摘要。",
        "tools": ["file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 2,
        "depends_on": [],
        "runtime_status": "running"
      }
    ]
  },
  "execution_logs": [],
    "workspace": {
      "workspace_path": "D:\\AI\\0000001-1\\workspace\\projects\\conversation_16\\workflow_7",
      "status": "running",
      "progress": 0,
      "active_node_id": null,
      "artifacts": [],
      "updated_at": "2026-05-13T02:11:00+00:00",
      "pause_after_nodes": ["node_1"]
    },
    "handoff_logs": [],
    "workflow_run": {
      "run_id": 12,
      "status": "running",
      "control_signal": "none",
      "checkpoint_node_id": null,
      "redirect_instruction": "",
      "saved_at": null
    },
    "error_report": null,
  "created_at": "2026-05-12T23:13:39Z",
  "updated_at": "2026-05-12T23:13:39Z"
}
```

说明：

- 当前版本只支持最小串行执行，不支持并发节点
- 执行过程通过 WebSocket `workflow_update` 和 `log` 事件回推到前端
- 前端在节点完成、失败和终态时会自动回拉工作流与消息历史，补齐 `execution_logs` 与节点摘要消息
- 当前节点会按 `template_id` 绑定预置角色模板，执行提示词和默认工具由模板提供
- 每个节点完成后会向当前对话追加一条角色摘要消息
- 每条工作流会在仓库根目录 `workspace/projects/conversation_<id>/workflow_<id>/` 创建共享工作区
- 同一对话下的多条工作流会共用 `workspace/projects/conversation_<id>/project_memory.json`
- 节点间交接会写入 `handoff_logs` 与 `context/handoff_log.json`
- 节点完成后会把摘要沉淀到 `project_memory.key_points`
- 若命中 `pause_after_nodes` 指定节点，工作流会进入 `waiting_confirm`，同时保存 `workflow_runs.checkpoint_json`
- 节点失败时会按 `max_retries` 自动重试；超过次数后回滚到最近安全快照，并以 `waiting_confirm + error_report` 形式等待人工恢复
- 人工修正后可通过 `redirect` 或 `resume` 重新执行失败节点；成功恢复后 `error_report` 会清空
- 执行完成后，`status` 会更新为 `completed`，并回写 `progress` 与 `execution_logs`

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `CONVERSATION_NOT_FOUND`
- `WORKFLOW_NOT_FOUND`
- `INVALID_WORKFLOW_STATUS`
- `EXECUTE_WORKFLOW_FAILED`

---

### POST /api/workflows/{conversation_id}/{workflow_id}/control

用途：对运行中的工作流发送暂停、恢复、中断或改向控制指令。

请求体：

```json
{
  "action": "resume",
  "redirect_instruction": ""
}
```

支持动作：

- `pause`
- `resume`
- `abort`
- `redirect`

成功响应：

```json
{
  "workflow_id": 25,
  "status": "waiting_confirm",
  "workflow_run": {
    "run_id": 8,
    "status": "waiting_confirm",
    "control_signal": "none",
    "checkpoint_node_id": "node_1",
    "redirect_instruction": "",
    "saved_at": "2026-05-13T01:35:00+00:00"
  },
  "error_report": {
    "failed_node_id": "node_1",
    "failed_role": "PM",
    "task": "梳理需求并输出可交接摘要",
    "error_message": "未知角色模板",
    "retry_count": 3,
    "max_retries": 2,
    "can_retry": false,
    "upstream_node_id": null,
    "upstream_role": "Manager",
    "rollback_checkpoint_node_id": "node_1",
    "rollback_progress": 0,
    "recovery_suggestion": "建议先修正节点配置，再通过 redirect 继续执行。"
  }
}
```

说明：

- `redirect` 时必须提供非空 `redirect_instruction`
- 工作流处于 `waiting_confirm` 时，推荐使用 `resume` 或 `redirect`
- 普通断点等待与错误恢复等待都会复用 `waiting_confirm`，可通过 `error_report` 是否为空区分
- 当前控制结果会同步回 `workflow_run`、`workspace` 和最近一次运行快照

错误码：

- `WORKFLOW_NOT_FOUND`
- `WORKFLOW_RUN_NOT_FOUND`
- `INVALID_WORKFLOW_CONTROL_ACTION`
- `MISSING_REDIRECT_INSTRUCTION`
- `CONTROL_WORKFLOW_FAILED`

## 5. 当前未实现但已规划的接口

以下接口仍处于规划阶段，暂未在当前仓库中实现：

- `/api/projects`
