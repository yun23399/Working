# CHANGELOG

## 2026-05-13

### 后端能力

- 新增系统运行配置接口 `/api/system-settings/runtime`
- 新增工作流并发控制器 `backend/app/core/runtime/workflow_concurrency.py`
- 工作流执行入口已接入系统级并发槽位校验，超限时返回 `WORKFLOW_CONCURRENCY_LIMIT_REACHED`
- 新增根目录 `.env` 中 `MAX_CONCURRENT_WORKFLOWS` 的读取、更新与实时重载能力
- 共享工作区新增 `context/runtime_logs.jsonl`，用于持久化当前工作流运行期结构化日志
- 新增工作流运行日志读取接口 `/api/workflows/{conversation_id}/{workflow_id}/runtime-logs`
- DAG 编排器在推送 WebSocket `log` 事件时会同步写入本地日志文件，并在每次重新执行前重置旧日志
- 新增用户自定义 Agent 角色模板表、服务层与 CRUD 接口
- 新增自定义 Agent 角色模板导出接口 `/api/agent-role-templates/export`
- 新增自定义 Agent 角色模板导入接口 `/api/agent-role-templates/import`
- 工作流重新规划时可按触发关键词引入启用中的自定义角色模板
- 工作流节点新增模板来源、模板摘要与触发关键词字段，执行阶段改为消费节点模板快照
- 新增本地系统通知器 `backend/app/notifications/notifier.py`
- 工作流开始执行、等待确认、完成和中断时会触发本地通知记录
- 新增 `NOTIFICATIONS_ENABLED` 与 `NOTIFICATION_SOUND_ENABLED` 环境变量
- 日志目录解析统一改为仓库根目录，通知日志固定写入 `logs/notifications.log`
- 新增共享工作区管理器 `workspace.py`
- 工作流新增 `workspace_path`、`workspace_state_json`、`handoff_log_json` 持久化字段
- 工作流执行时会在仓库根目录 `workspace/projects/...` 初始化专属工作区
- 节点执行前后会回写工作区状态快照和节点交接记录
- 工作流接口响应新增 `workspace` 与 `handoff_logs`
- 新增工作流运行记录表 `workflow_runs`
- 新增断点控制器 `checkpoint.py`
- 新增工作流控制接口 `/api/workflows/{conversation_id}/{workflow_id}/control`
- 工作流已支持 `waiting_confirm` 断点等待、恢复执行与人工改向信号
- 新增工作流错误处理器 `error_handler.py`
- 工作流节点失败后已支持自动重试、快照回滚、层级上报与恢复建议
- 工作流响应新增 `error_report`，前端卡片可直接展示错误恢复信息
- 新增项目级记忆管理器 `project_memory.py`
- 工作流响应新增 `project_memory`，同一对话下可跨工作流复用长期目标、关键摘要与最近异常
- 新增工具基类 `base_tool.py`
- 新增最小代码执行工具 `code_executor.py`
- 新增最小文件读写工具 `file_tool.py`
- 角色模板命中 `file_tool` 时会在共享工作区 `artifacts/` 生成真实摘要文件
- 新增最小外部 API 调用工具 `api_caller.py`
- 后端模板命中 `api_caller` 时会在共享工作区 `artifacts/` 生成真实接口响应文件
- 新增最小浏览器自动化工具 `browser_tool.py`
- 前端与测试模板命中 `browser_tool` 时会在共享工作区 `artifacts/` 生成真实截图和浏览器结果文件
- 新增最小图像工具 `image_tool.py`
- 设计师模板命中 `image_tool` 时会在共享工作区 `artifacts/` 生成真实设计图片和图像结果文件
- `backend` / `frontend` 模板命中 `code_executor` 时会在共享工作区 `artifacts/` 生成真实计划文件
- `workspace.artifacts` 与节点 `execution_logs[].artifacts` 已支持返回真实产物路径
- 新增受保护工作流产物接口 `/api/workflows/{conversation_id}/{workflow_id}/artifacts`
- 新增受保护工作流产物文件接口 `/api/workflows/{conversation_id}/{workflow_id}/artifacts/file`
- 新增工作流产物导出接口 `/api/workflows/{conversation_id}/{workflow_id}/artifacts/export`
- 修复 Windows 下代码执行工具在 `uvicorn --reload` 环境中的子进程兼容问题
- 修复 Windows 下浏览器工具在 `uvicorn --reload` 环境中的 Playwright 子进程兼容问题
- 新增图像工具在缺少 `OPENAI_API_KEY` 时的本地占位图回退链路，保证阶段三回归可执行

### 前端能力

- 设置页新增“工作流并发上限”面板，可查看当前上限、执行中数量、剩余槽位与是否已满
- 设置页支持修改工作流并发上限，并调用系统运行配置接口实时保存
- 设置页升级为自定义 Agent 角色模板管理入口，支持创建、编辑、启停与删除
- 设置页新增角色模板 JSON 导入/导出入口，支持“跳过同名角色”和“覆盖同名角色”两种导入策略
- 工作流预览卡片新增模板来源展示，可区分内置模板与自定义角色
- 聊天页新增当前对话内搜索栏，支持关键词匹配、高亮与上下跳转
- `MessageBubble` 新增消息关键词高亮与搜索焦点态展示
- 切换对话后会自动重置搜索状态，避免跨对话残留
- 项目页升级为本地多项目管理入口，支持搜索、创建、编辑、删除与对话迁移
- `projectStore` 新增本地项目增删改与对话重分组能力
- 从项目页打开指定对话时，聊天页会保留已选项目与对话上下文
- 新增工作流运行日志面板 `LogViewer`
- 聊天页改为分离聊天日志与工作流编排日志
- 新增工作流产物预览面板 `ArtifactPreviewPanel`
- 新增 `CodePreview`、`ImagePreview`、`DocumentPreview` 三类真实产物预览组件
- 聊天页可直接读取并预览当前工作流的代码、文档与图片产物
- 聊天页产物面板新增“导出产物”按钮，可一键下载当前工作流全部真实产物压缩包
- 新增 `TokenCounter` 组件，并将聊天头部 Token 用量展示抽离为独立组件
- `workflowStore` 新增按工作流缓存运行时日志的状态管理
- `useWebSocket` 新增日志事件回调扩展点，支持页面侧按场景消费 `log` 事件
- 工作流重新执行前会清空当前运行日志，避免旧日志残留
- 工作流日志面板新增 `DEBUG / INFO / WARNING / ERROR` 分级过滤、关键词搜索与时间戳展示
- 工作流日志面板新增导出当前筛选结果为 `workflow-runtime-logs.txt`
- 聊天页在进入或切换工作流时会自动回填日志文件中的最近运行记录
- 工作流卡片新增暂停、恢复、改向与中断操作入口

## 2026-05-12

### 文档与流程

- 新增项目级 `README.md`
- 新增 API 契约文档
- 新增 WebSocket 协议文档
- 新增产品流程文档
- 新增测试与验收文档
- 新增部署文档
- 新增 `DESIGN_SYSTEM.md`
- 新增 `PAGE_STRUCTURE.md`
- 新增 `FRONTEND_SPEC.md`
- 优化阶段一执行顺序，改为仓库状态对齐与最小闭环优先

### 仓库准备

- 新增 `.env.example`
- 新增 `.gitignore`
- 新增 GitHub Actions 基础工作流

### 后端能力

- 实现 JWT + bcrypt 认证闭环
- 实现统一错误响应格式
- 实现 loguru 控制台与文件日志
- 实现对话与消息模型
- 实现最小对话接口与消息持久化
- 实现对话级 WebSocket 连接管理
- 实现统一 LLM 适配层
- 实现 Manager Agent 真实流式回复
- 为 Ollama 增加原生聊天流式兼容路径
- 新增 Alembic 真实表结构迁移
- 新增本地开发 CORS 配置

### 前端能力

- 实现登录/注册页面
- 实现本地登录态持久化
- 实现聊天页真实对话列表和消息列表
- 实现 WebSocket 连接、自动重连和流式展示
- 实现实时日志展示与错误提示
- 实现最小聊天闭环联调
- 实现最小项目分组、本地项目映射和历史视图切换
- 新增项目页与聊天页之间的最小项目导航
- 固定前端默认开发端口并读取仓库根目录环境配置
- 新增工作流预览确认卡片
- 新增工作流预览状态管理与确认交互

### 阶段二最小链路

- 新增需求提取器 `requirement_extractor.py`
- 新增工作流规划器 `workflow_planner.py`
- 新增工作流模型、Schema、服务层与 API 路由
- 新增 `workflows` 表 Alembic 迁移
- 聊天页接入“生成预览 / 重新规划 / 确认工作流”闭环
- 文档同步到当前阶段二最小工作流预览实现

### 阶段二执行增量

- 新增最小 DAG 编排器 `dag_orchestrator.py`
- 新增最小 Agent 生成器 `agent_spawner.py`
- 新增通用执行 Agent 运行时
- 工作流支持 `progress` 与 `execution_logs`
- 新增工作流执行接口 `/api/workflows/{conversation_id}/{workflow_id}/execute`
- 前端工作流卡片新增开始执行、进度条、节点状态与交接摘要展示
- 前端在执行过程中可自动刷新工作流与消息历史，补齐节点摘要与执行日志
- 工作流接口响应补充节点 `runtime_status`，避免前端刷新后状态回退
- 新增 PM / 前端 / 后端 / 测试 / 设计师预置角色模板与动态选角链路
