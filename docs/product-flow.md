# 产品主流程文档

本文档描述当前项目已经实现的主流程，以及后续阶段的扩展路线。

## 1. 登录流程

1. 用户打开登录页
2. 选择登录或注册模式
3. 调用 `/api/auth/register` 或 `/api/auth/login`
4. 登录成功后保存 JWT 与用户信息到本地存储
5. 跳转到聊天页
6. 聊天页通过 `/api/auth/me` 恢复用户信息

失败分支：

- 认证失败：显示接口错误提示
- 网络失败：显示“请确认后端服务已启动”

## 2. 对话启动流程

1. 前端进入聊天页
2. 调用 `/api/conversations` 获取当前用户的对话列表
3. 若列表为空，则自动创建第一条对话
4. 若列表非空，则自动加载第一条对话的消息历史
5. 前端建立 `/ws/{conversation_id}` 实时连接

说明：

- 当前左侧“项目列表”为界面占位数据
- 当前真实持久化实体为“用户、对话、消息”

## 3. 当前阶段一对话流程

1. 用户在聊天输入框中发送消息
2. 前端调用 `POST /api/conversations/{id}/chat`
3. 后端保存用户消息
4. 后端启动模拟 Manager 回复任务
5. 后端通过 WebSocket 推送 `log`
6. 后端推送 `agent_status=running`
7. 后端持续推送 `token`
8. 前端实时拼接并展示流式消息
9. 后端推送 `agent_status=done`
10. 完整回复持久化到数据库
11. 对话 `updated_at` 刷新，历史列表排序更新

## 4. 错误恢复流程

1. 若 HTTP 请求失败，前端显示统一错误提示
2. 若 Token 失效，前端清空本地登录态并跳回登录页
3. 若 WebSocket 断开，前端最多自动重连 3 次
4. 若 3 次重连仍失败，前端保留消息并提示用户手动刷新或重新进入对话

## 5. 阶段二扩展流程

阶段二开始后，主流程会从“普通对话”扩展为“工作流协作”：

1. Manager 判断需求是否明确
2. 需求提取器生成结构化需求
3. 工作流规划器生成 DAG
4. 前端展示工作流确认卡片
5. 用户确认后进入多 Agent 并发执行
6. 前端实时展示状态、日志与产出物

## 6. 当前状态机建议

### 对话状态

- `idle`
- `connecting`
- `sending`
- `streaming`
- `completed`
- `error`

### 工作流状态

- `collecting_requirements`
- `ready_to_plan`
- `awaiting_confirmation`
- `running`
- `paused`
- `failed`
- `completed`
