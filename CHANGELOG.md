# CHANGELOG

## 2026-05-13

### 前端能力

- 新增工作流运行日志面板 `LogViewer`
- 聊天页改为分离聊天日志与工作流编排日志
- `workflowStore` 新增按工作流缓存运行时日志的状态管理
- `useWebSocket` 新增日志事件回调扩展点，支持页面侧按场景消费 `log` 事件
- 工作流重新执行前会清空当前运行日志，避免旧日志残留

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
