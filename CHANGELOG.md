# CHANGELOG

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
