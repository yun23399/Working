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

## 4. 系统运行配置接口

### GET /api/system-settings/plugins

用途：读取当前仓库已安装的本地插件列表，供设置页展示插件能力与启停状态。

成功响应：

```json
[
  {
    "plugin_id": "research-helper",
    "name": "研究助理插件",
    "description": "为包含调研、竞品和资料整理需求的工作流提供研究助理角色模板。",
    "version": "1.0.0",
    "tools": ["file_tool", "api_caller"],
    "agent_templates": [
      {
        "template_id": "plugin:research-helper:research-analyst",
        "role_name": "研究助理",
        "summary": "负责资料检索、竞品整理、证据归纳与对比结论输出。",
        "trigger_keywords": ["调研", "研究", "竞品", "资料", "research"],
        "default_tools": ["file_tool", "api_caller"]
      }
    ],
    "source_path": "D:\\AI\\0000001-1\\plugins\\examples\\research_helper",
    "is_enabled": true
  }
]
```

说明：

- 当前插件目录来源于仓库根目录 `plugins/` 与 `plugins/examples/`
- `tools` 当前为声明式展示字段，供设置页说明插件宣称能力
- `agent_templates` 是当前阶段的真实生效能力，启用后会并入工作流规划链路

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `LIST_PLUGINS_FAILED`

### PUT /api/system-settings/plugins/{plugin_id}

用途：更新指定本地插件的启停状态，并将结果写回仓库根目录 `.env` 的 `ENABLED_PLUGINS`。

请求体：

```json
{
  "is_enabled": false
}
```

成功响应：

```json
{
  "plugin_id": "research-helper",
  "name": "研究助理插件",
  "description": "为包含调研、竞品和资料整理需求的工作流提供研究助理角色模板。",
  "version": "1.0.0",
  "tools": ["file_tool", "api_caller"],
  "agent_templates": [
    {
      "template_id": "plugin:research-helper:research-analyst",
      "role_name": "研究助理",
      "summary": "负责资料检索、竞品整理、证据归纳与对比结论输出。",
      "trigger_keywords": ["调研", "研究", "竞品", "资料", "research"],
      "default_tools": ["file_tool", "api_caller"]
    }
  ],
  "source_path": "D:\\AI\\0000001-1\\plugins\\examples\\research_helper",
  "is_enabled": false
}
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `PLUGIN_NOT_FOUND`
- `UPDATE_PLUGIN_STATE_FAILED`

### GET /api/system-settings/runtime

用途：读取当前系统级工作流并发配置和运行槽位快照。

成功响应：

```json
{
  "max_concurrent_workflows": 3,
  "active_workflow_count": 1,
  "remaining_slots": 2,
  "is_limit_reached": false
}
```

说明：

- 当前配置来源于仓库根目录 `.env` 的 `MAX_CONCURRENT_WORKFLOWS`
- 当前实现为单进程内存级并发槽位控制，适用于本地单实例运行
- `remaining_slots=0` 时，新的工作流执行请求会被拒绝

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `GET_SYSTEM_RUNTIME_SETTINGS_FAILED`

### PUT /api/system-settings/runtime

用途：更新当前系统级工作流并发上限，并让当前后端进程立即生效。

请求体：

```json
{
  "max_concurrent_workflows": 2
}
```

成功响应：

```json
{
  "max_concurrent_workflows": 2,
  "active_workflow_count": 1,
  "remaining_slots": 1,
  "is_limit_reached": false
}
```

说明：

- 当前仅允许设置 `1` 到 `10` 之间的整数
- 更新时只会改写 `.env` 中的 `MAX_CONCURRENT_WORKFLOWS`，不会覆盖其它环境变量
- 当前进程会在保存后立即重新载入配置

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `VALIDATION_ERROR`
- `UPDATE_SYSTEM_RUNTIME_SETTINGS_FAILED`

---

## 5. 工作流接口

## 5.1 自定义 Agent 角色模板接口

### GET /api/agent-role-templates

用途：获取当前用户的全部自定义 Agent 角色模板。

成功响应：

```json
[
  {
    "template_id": "user-1-devops",
    "role_name": "运维工程师",
    "summary": "负责部署、监控、告警和运行环境检查。",
    "system_prompt": "你是运维工程师，重点关注部署、环境稳定性、监控和回滚策略。",
    "trigger_keywords": ["运维", "部署", "监控"],
    "default_tools": ["file_tool", "api_caller"],
    "max_retries": 2,
    "is_enabled": true,
    "created_at": "2026-05-13T09:00:00Z",
    "updated_at": "2026-05-13T09:00:00Z"
  }
]
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `LIST_AGENT_ROLE_TEMPLATES_FAILED`

### POST /api/agent-role-templates

用途：创建当前用户的自定义 Agent 角色模板。

请求体：

```json
{
  "role_name": "运维工程师",
  "summary": "负责部署、监控、告警和运行环境检查。",
  "system_prompt": "你是运维工程师，重点关注部署、环境稳定性、监控和回滚策略。",
  "trigger_keywords": ["运维", "部署", "监控"],
  "default_tools": ["file_tool", "api_caller"],
  "max_retries": 2,
  "is_enabled": true
}
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `VALIDATION_ERROR`
- `AGENT_ROLE_TEMPLATE_CONFLICT`
- `CREATE_AGENT_ROLE_TEMPLATE_FAILED`

### PUT /api/agent-role-templates/{template_id}

用途：更新当前用户的指定自定义 Agent 角色模板。

请求体：

```json
{
  "role_name": "运维工程师",
  "summary": "负责部署、监控、告警和运行环境检查。",
  "system_prompt": "你是运维工程师，重点关注部署、环境稳定性、监控和回滚策略。",
  "trigger_keywords": ["运维", "部署", "监控", "告警"],
  "default_tools": ["file_tool", "api_caller"],
  "max_retries": 3,
  "is_enabled": true
}
```

成功响应：

```json
{
  "template_id": "user-1-devops",
  "role_name": "运维工程师",
  "summary": "负责部署、监控、告警和运行环境检查。",
  "system_prompt": "你是运维工程师，重点关注部署、环境稳定性、监控和回滚策略。",
  "trigger_keywords": ["运维", "部署", "监控", "告警"],
  "default_tools": ["file_tool", "api_caller"],
  "max_retries": 3,
  "is_enabled": true,
  "created_at": "2026-05-13T09:00:00Z",
  "updated_at": "2026-05-13T09:30:00Z"
}
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `VALIDATION_ERROR`
- `AGENT_ROLE_TEMPLATE_NOT_FOUND`
- `AGENT_ROLE_TEMPLATE_CONFLICT`
- `UPDATE_AGENT_ROLE_TEMPLATE_FAILED`

### DELETE /api/agent-role-templates/{template_id}

用途：删除当前用户的指定自定义 Agent 角色模板。

成功响应：

- `204 No Content`

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `AGENT_ROLE_TEMPLATE_NOT_FOUND`
- `DELETE_AGENT_ROLE_TEMPLATE_FAILED`

### GET /api/agent-role-templates/export

用途：导出当前用户的全部自定义 Agent 角色模板，返回可复用的 JSON 配置包。

成功响应：

```json
{
  "version": "1.0",
  "exported_at": "2026-05-13T10:00:00Z",
  "template_count": 1,
  "templates": [
    {
      "template_id": "user-1-devops",
      "role_name": "运维工程师",
      "summary": "负责部署、监控、告警和运行环境检查。",
      "system_prompt": "你是运维工程师，重点关注部署、环境稳定性、监控和回滚策略。",
      "trigger_keywords": ["运维", "部署", "监控"],
      "default_tools": ["file_tool", "api_caller"],
      "max_retries": 2,
      "is_enabled": true,
      "created_at": "2026-05-13T09:00:00Z",
      "updated_at": "2026-05-13T09:00:00Z"
    }
  ]
}
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `EXPORT_AGENT_ROLE_TEMPLATES_FAILED`

### POST /api/agent-role-templates/import

用途：导入角色模板配置，并按冲突策略创建或覆盖当前用户的同名角色模板。

请求体：

```json
{
  "conflict_strategy": "skip",
  "bundle": {
    "version": "1.0",
    "templates": [
      {
        "role_name": "运维工程师",
        "summary": "负责部署、监控、告警和运行环境检查。",
        "system_prompt": "你是运维工程师，重点关注部署、环境稳定性、监控和回滚策略。",
        "trigger_keywords": ["运维", "部署", "监控"],
        "default_tools": ["file_tool", "api_caller"],
        "max_retries": 2,
        "is_enabled": true
      }
    ]
  }
}
```

说明：

- `conflict_strategy=skip` 时，若检测到同名角色，会保留当前账号已有模板并跳过导入项
- `conflict_strategy=overwrite` 时，若检测到同名角色，会覆盖当前账号已有模板内容
- 导入结果会逐条返回 `created / updated / skipped` 状态，便于前端回显

成功响应：

```json
{
  "total_count": 2,
  "created_count": 1,
  "updated_count": 0,
  "skipped_count": 1,
  "results": [
    {
      "role_name": "运维工程师",
      "template_id": "user-1-devops",
      "status": "skipped",
      "message": "检测到同名角色，已按跳过策略保留现有模板"
    },
    {
      "role_name": "测试工程师",
      "template_id": "user-1-qa-reviewer",
      "status": "created",
      "message": "已创建新角色模板"
    }
  ]
}
```

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `VALIDATION_ERROR`
- `AGENT_ROLE_TEMPLATE_CONFLICT`
- `IMPORT_AGENT_ROLE_TEMPLATES_FAILED`

---

## 5. 工作流接口

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
          "template_source": "builtin",
          "template_summary": "负责梳理需求目标、约束和可交付范围，产出清晰执行摘要。",
          "role": "需求分析师",
          "task": "梳理目标、约束与交付范围，输出执行摘要。",
          "tools": ["file_tool"],
          "llm": "ollama/qwen2.5-coder:3b",
          "max_retries": 2,
          "depends_on": [],
          "trigger_keywords": ["需求", "规划", "阶段", "计划", "排期"],
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

### GET /api/workflows/{conversation_id}/{workflow_id}/artifacts

用途：获取指定工作流当前可见的真实产物列表，供前端选择代码、文档或图片预览目标。

成功响应：

```json
[
  {
    "name": "design_mockup.png",
    "relative_path": "design_mockup.png",
    "preview_type": "image",
    "mime_type": "image/png",
    "size_bytes": 367363,
    "updated_at": "2026-05-13T04:28:00+00:00"
  },
  {
    "name": "design_brief.md",
    "relative_path": "design_brief.md",
    "preview_type": "document",
    "mime_type": "text/markdown",
    "size_bytes": 845,
    "updated_at": "2026-05-13T04:28:00+00:00"
  }
]
```

说明：

- 当前接口会优先汇总 `workspace.artifacts`，并补齐磁盘 `artifacts/` 目录中的真实文件
- `relative_path` 仅允许定位到当前工作流的 `artifacts/` 目录内文件
- `preview_type` 当前支持 `code / document / image / binary`

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `CONVERSATION_NOT_FOUND`
- `WORKFLOW_NOT_FOUND`
- `LIST_WORKFLOW_ARTIFACTS_FAILED`

### GET /api/workflows/{conversation_id}/{workflow_id}/artifacts/file

用途：按相对路径读取指定工作流下的单个真实产物文件内容，供前端做图片或文本预览。

查询参数：

```text
path=design_brief.md
```

成功响应：

- 图片文件返回对应二进制流，例如 `image/png`
- 文本文件返回文本流，例如 `text/markdown; charset=utf-8`

说明：

- 当前接口要求 `path` 必须位于当前工作流的 `artifacts/` 目录内
- 前端会基于上一个接口返回的 `relative_path` 调用当前接口
- 2026-05-13 实测通过：`conversation_50 / workflow_48` 可读取 `design_mockup.png` 与 `design_brief.md`

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `CONVERSATION_NOT_FOUND`
- `WORKFLOW_NOT_FOUND`
- `WORKFLOW_ARTIFACT_NOT_FOUND`
- `INVALID_WORKFLOW_ARTIFACT_PATH`
- `GET_WORKFLOW_ARTIFACT_FAILED`

### GET /api/workflows/{conversation_id}/{workflow_id}/artifacts/export

用途：导出指定工作流当前全部真实产物，返回 zip 压缩包下载流。

成功响应：

- `application/zip` 二进制流

说明：

- 当前接口仅导出当前工作流 `artifacts/` 目录内的真实文件
- 压缩包会临时生成在当前工作流的 `exports/` 目录下
- 压缩包文件名格式为 `workflow_<workflow_id>_artifacts.zip`

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `CONVERSATION_NOT_FOUND`
- `WORKFLOW_NOT_FOUND`
- `EMPTY_WORKFLOW_ARTIFACTS`
- `INVALID_WORKFLOW_EXPORT_PATH`
- `EXPORT_WORKFLOW_ARTIFACTS_FAILED`

### GET /api/workflows/{conversation_id}/{workflow_id}/runtime-logs

用途：读取指定工作流最近的运行日志列表，供前端日志面板回填历史、分级过滤和导出。

查询参数：

```text
limit=200
```

成功响应：

```json
[
  {
    "id": "2026-05-13T12:00:00+00:00-orchestrator",
    "level": "INFO",
    "message": "工作流已进入执行阶段，开始按节点顺序推进",
    "agent_id": "orchestrator",
    "timestamp": "2026-05-13T12:00:00+00:00"
  },
  {
    "id": "2026-05-13T12:00:01+00:00-node_1",
    "level": "WARNING",
    "message": "需求分析师 即将开始第 2 次尝试",
    "agent_id": "node_1",
    "timestamp": "2026-05-13T12:00:01+00:00"
  }
]
```

说明：

- 日志来源于当前工作流共享工作区 `context/runtime_logs.jsonl`
- 后端在推送 WebSocket `log` 事件时，会同步将结构化日志写入该文件
- 当前接口默认最多返回最近 `200` 条记录，便于页面刷新或重新进入工作流后快速回填
- 每次重新执行当前工作流前，编排器都会先清空旧的日志文件，保证历史回填与本轮执行一致

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `CONVERSATION_NOT_FOUND`
- `WORKFLOW_NOT_FOUND`
- `GET_WORKFLOW_RUNTIME_LOGS_FAILED`

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
        "template_source": "builtin",
        "template_summary": "负责梳理需求目标、约束和可交付范围，产出清晰执行摘要。",
        "role": "需求分析师",
        "task": "梳理目标、约束与交付范围，输出执行摘要。",
        "tools": ["file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 2,
        "depends_on": [],
        "trigger_keywords": ["需求", "规划", "阶段", "计划", "排期"],
        "runtime_status": "waiting"
      },
      {
        "id": "node_2",
        "template_id": "frontend",
        "template_source": "builtin",
        "template_summary": "负责页面结构、交互流程与前端实现规划。",
        "role": "方案规划师",
        "task": "根据需求摘要生成实施方案、任务拆分和风险提示。",
        "tools": ["file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 2,
        "depends_on": ["node_1"],
        "trigger_keywords": ["前端", "页面", "界面", "交互", "ui", "frontend"],
        "runtime_status": "waiting"
      },
      {
        "id": "node_3",
        "template_id": "backend",
        "template_source": "builtin",
        "template_summary": "负责接口、数据结构和执行逻辑的后端交付。",
        "role": "交付执行者",
        "task": "根据确认后的方案产出最终交付物草稿，并整理交接说明。",
        "tools": ["code_executor", "file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 3,
        "depends_on": ["node_2"],
        "trigger_keywords": ["后端", "接口", "服务", "数据库", "api", "backend"],
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
- 节点会同时返回 `template_id`、`template_source`、`template_summary` 与 `trigger_keywords`
- `template_source` 当前取值为 `builtin` 或 `custom`，用于区分内置模板和用户自定义角色
- 当前阶段会同时返回共享工作区 `workspace` 状态和节点交接记录 `handoff_logs`
- 当前阶段会返回 `project_memory`，用于展示同一对话下跨工作流复用的长期上下文
- 当前阶段会返回 `workflow_run`，用于展示运行轮次与断点状态
- 当工作流因节点失败进入人工恢复阶段时，会额外返回 `error_report`
- 工作流重新规划时会自动读取当前用户已启用的自定义角色模板，并按触发关键词匹配后追加到节点序列
- 工作流重新规划时还会自动读取当前已启用插件提供的角色模板，并按触发关键词匹配后追加到节点序列
- 插件模板节点的 `template_source` 会返回 `plugin`
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
        "template_source": "builtin",
        "template_summary": "负责梳理需求目标、约束和可交付范围，产出清晰执行摘要。",
        "role": "需求分析师",
        "task": "梳理目标、约束与交付范围，输出执行摘要。",
        "tools": ["file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 2,
        "depends_on": [],
        "trigger_keywords": ["需求", "规划", "阶段", "计划", "排期"],
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
        "template_source": "builtin",
        "template_summary": "负责梳理需求目标、约束和可交付范围，产出清晰执行摘要。",
        "role": "需求分析师",
        "task": "梳理目标、约束与交付范围，输出执行摘要。",
        "tools": ["file_tool"],
        "llm": "ollama/qwen2.5-coder:3b",
        "max_retries": 2,
        "depends_on": [],
        "trigger_keywords": ["需求", "规划", "阶段", "计划", "排期"],
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
- 工作流开始新一轮执行前，会先清空共享工作区 `context/runtime_logs.jsonl` 中的旧日志
- 当前节点执行时不再依赖实时查找内置模板，而是直接消费预览阶段写入节点的模板快照
- 节点模板快照包含 `template_id`、`template_source`、`template_summary`、`template_system_prompt` 与 `trigger_keywords`
- 每个节点完成后会向当前对话追加一条角色摘要消息
- 每条工作流会在仓库根目录 `workspace/projects/conversation_<id>/workflow_<id>/` 创建共享工作区
- 当前 `pm` / `qa` / `designer` 等模板命中 `file_tool` 时，会在 `artifacts/` 下真实生成 `.md` 摘要文件
- 当前 `backend` 模板命中 `api_caller` 时，会在 `artifacts/` 下真实生成 `api_response.json`
- 当前 `backend` 与 `frontend` 模板命中 `code_executor` 时，会在 `artifacts/` 下真实生成计划文件
- 当前 `frontend` 与 `qa` 模板命中 `browser_tool` 时，会在 `artifacts/` 下真实生成截图与浏览器结果文件
- 当前 `designer` 模板命中 `image_tool` 时，会在 `artifacts/` 下真实生成设计图片与图像结果文件
- 同一对话下的多条工作流会共用 `workspace/projects/conversation_<id>/project_memory.json`
- 节点间交接会写入 `handoff_logs` 与 `context/handoff_log.json`
- 编排器与节点运行日志会同时进入 WebSocket 与 `context/runtime_logs.jsonl`，供页面刷新后回填
- 节点完成后会把摘要沉淀到 `project_memory.key_points`
- 若命中 `pause_after_nodes` 指定节点，工作流会进入 `waiting_confirm`，同时保存 `workflow_runs.checkpoint_json`
- 节点失败时会按 `max_retries` 自动重试；超过次数后回滚到最近安全快照，并以 `waiting_confirm + error_report` 形式等待人工恢复
- 人工修正后可通过 `redirect` 或 `resume` 重新执行失败节点；成功恢复后 `error_report` 会清空
- 执行完成后，`status` 会更新为 `completed`，并回写 `progress`、`execution_logs` 与 `workspace.artifacts`
- 2026-05-13 实测通过：`workspace.artifacts` 可同时返回 `backend_plan.json` 与 `code_execution_result.json`
- 2026-05-13 实测通过：`workspace.artifacts` 可同时返回 `pm_summary.md`、`backend_summary.md`、`backend_plan.json` 与 `code_execution_result.json`
- 2026-05-13 实测通过：`workspace.artifacts` 可同时返回 `api_response.json`、`pm_summary.md`、`backend_summary.md`、`backend_plan.json` 与 `code_execution_result.json`
- 2026-05-13 实测通过：`conversation_48 / workflow_47` 执行完成后，`workspace.artifacts` 可同时返回 `frontend_snapshot.png`、`frontend_browser_result.json`、`qa_snapshot.png` 与 `qa_browser_result.json`
- 2026-05-13 实测通过：`conversation_50 / workflow_48` 执行完成后，`workspace.artifacts` 可同时返回 `design_brief.md`、`design_mockup.png` 与 `design_image_result.json`

错误码：

- `MISSING_TOKEN`
- `INVALID_TOKEN`
- `USER_NOT_FOUND`
- `CONVERSATION_NOT_FOUND`
- `WORKFLOW_NOT_FOUND`
- `INVALID_WORKFLOW_STATUS`
- `WORKFLOW_CONCURRENCY_LIMIT_REACHED`
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

- `CONVERSATION_NOT_FOUND`
- `WORKFLOW_NOT_FOUND`
- `WORKFLOW_RUN_NOT_FOUND`
- `INVALID_WORKFLOW_CONTROL_ACTION`
- `MISSING_REDIRECT_INSTRUCTION`
- `CONTROL_WORKFLOW_FAILED`

## 6. 当前未实现但已规划的接口

以下接口仍处于规划阶段，暂未在当前仓库中实现：

- `/api/projects`
