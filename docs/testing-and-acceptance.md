# 测试与验收文档

## 阶段一验收目标

阶段一的验收标准不是“文件存在”，而是“最小聊天闭环可跑通”。

当前已验证的链路：

1. 前端依赖安装成功
2. 前端 lint 通过
3. 前端 build 通过
4. 后端依赖安装成功
5. 后端 `ruff check .` 通过
6. 后端 `black --check .` 通过
7. Alembic 真实迁移可执行
8. 后端服务可启动
9. 注册、登录、鉴权可用
10. 对话创建与历史消息接口可用
11. 最小项目分组与历史视图可用
12. WebSocket 流式消息可用
13. 浏览器中可完成登录、项目切换与聊天联调
14. 工作流预览生成、重新规划与确认链路可用
15. 最小工作流执行链路可用
16. 工作流实时日志面板可用
17. 共享工作区链路可用
18. 断点控制链路可用
19. 错误恢复与人工改向链路可用
20. 项目级记忆链路可用

## 建议命令

### 前端

```powershell
cd frontend
npm install
npm run lint
npm run build
```

### 后端

```powershell
cd backend
pip install -r requirements.txt
ruff check .
black --check .
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 浏览器联调前准备

如果本机第一次执行 Playwright 浏览器自动化，需要先安装浏览器运行时：

```powershell
cd backend
python -m playwright install chromium
```

## 当前已完成的实测结果

### 用例 1：注册与登录

验证结果：

- `/api/auth/register` 返回 `201`
- `/api/auth/login` 返回 `200`
- `/api/auth/me` 可返回当前用户

### 用例 2：创建对话与读取消息

验证结果：

- `/api/conversations` 返回 `200`
- `POST /api/conversations` 返回 `201`
- `/api/conversations/{id}/messages` 返回 `200`

### 用例 3：WebSocket 流式回复

验证结果：

- `POST /api/conversations/{id}/chat` 返回 `200`
- 已接收到事件序列：`agent_status(running) -> log -> token -> ... -> agent_status(done)`
- assistant 最终消息已持久化
- 当前回复由真实 Manager Agent 流式生成

### 用例 4：统一错误格式

验证结果：

- 参数校验失败时返回 `422`
- 响应结构已统一为 `error / code / detail`

### 用例 5：浏览器真实联调

验证结果：

- 登录页可访问
- 可从注册模式成功进入聊天页
- 可切换到无历史对话的项目并保持空状态
- 可在当前项目下创建新对话
- 聊天页可发送消息
- 浏览器内可看到 Manager 流式回复
- 切回其他项目后仅展示该项目下的历史对话
- 项目页可展示最小项目卡片并返回聊天页

### 用例 6：LLM 配置与提供商选择

建议验证：

- 设置 `LLM_PROVIDER=ollama` 且本地 Ollama 可用时，可正常获得流式回复
- 设置 `LLM_PROVIDER=openai` 但未配置 `OPENAI_API_KEY` 时，前端应收到明确错误提示

### 用例 7：阶段二工作流预览链路

验证结果：

- `POST /api/workflows/{conversation_id}/preview` 返回 `200`
- `GET /api/workflows/{conversation_id}` 可返回预览历史
- `POST /api/workflows/{conversation_id}/{workflow_id}/confirm` 返回 `200`
- 强制重新规划后会生成新的 `workflow_id`
- 当前最新预览可在聊天页工作流卡片中显示
- 当前阶段确认后仅更新状态，不启动真实 DAG 执行

### 用例 8：阶段二最小工作流执行链路

验证结果：

- `POST /api/workflows/{conversation_id}/{workflow_id}/execute` 返回 `200`
- 工作流状态可从 `confirmed` 进入 `running` 再进入 `completed`
- `progress` 最终到达 `100`
- `execution_logs` 会累计 3 条节点交接摘要
- 对话历史会追加 3 条节点执行结果消息
- WebSocket 已接入 `workflow_update` 事件，前端可消费节点状态
- 前端在节点完成与终态后可自动补齐 `execution_logs` 和节点摘要消息
- 包含前端/后端/设计/测试关键词的需求可生成对应角色模板节点

### 用例 9：阶段二工作流日志面板

验证结果：

- WebSocket `log` 事件中的 `orchestrator` 与 `node_*` 日志可实时展示在独立日志面板
- 聊天窗口日志区仅保留 `system` 与 `manager` 相关日志
- 再次执行同一工作流前，旧的运行时日志会被清空
- 工作流执行完成后，日志面板条数与运行期事件一致

### 用例 10：阶段二共享工作区链路

验证结果：

- `python -m alembic upgrade head` 可正常升级共享工作区相关字段
- 工作流执行后会在仓库根目录生成 `workspace/projects/conversation_<id>/workflow_<id>/`
- `context/workspace_state.json` 可记录当前状态、进度、活跃节点与产出物列表
- `context/handoff_log.json` 可记录节点之间的交接摘要
- `GET /api/workflows/{conversation_id}` 返回的 `workspace` 与 `handoff_logs` 字段可反映当前工作区状态

### 用例 11：阶段二断点控制链路

验证结果：

- `python -m alembic upgrade head` 可正常创建 `workflow_runs` 表
- `POST /api/workflows/{conversation_id}/preview` 可接受 `pause_after_nodes`
- `POST /api/workflows/{conversation_id}/{workflow_id}/execute` 后，命中断点节点可进入 `waiting_confirm`
- `POST /api/workflows/{conversation_id}/{workflow_id}/control` 发送 `resume` 后，工作流可继续到 `completed`
- `workflow_run.checkpoint_node_id` 与 `workflow_run.status` 可反映当前断点位置和运行状态

### 用例 12：阶段二错误恢复链路

验证结果：

- 节点执行失败时会按 `max_retries` 自动重试
- 超过最大重试次数后，工作流会进入 `waiting_confirm`
- `GET /api/workflows/{conversation_id}` 返回的 `error_report` 可包含失败节点、错误原因、上级角色、回滚进度与恢复建议
- 修正失败节点配置后，`POST /api/workflows/{conversation_id}/{workflow_id}/control` 发送 `redirect` 可重新执行失败节点
- 实测通过：`waiting_confirm + error_report -> redirect -> completed`

### 用例 13：阶段二项目级记忆链路

验证结果：

- `POST /api/workflows/{conversation_id}/preview` 后即可返回 `project_memory`
- 同一对话目录下会生成 `workspace/projects/conversation_<id>/project_memory.json`
- 工作流执行完成后，`project_memory.key_points` 会追加节点摘要
- `GET /api/workflows/{conversation_id}` 返回的 `project_memory` 可反映最新长期目标、关键记忆与最近异常

## 本地验证注意事项

### 1. 代理环境干扰

若使用 `httpx` 做本地接口验证，建议显式关闭环境代理：

```python
httpx.AsyncClient(trust_env=False)
```

否则本地 `127.0.0.1` 请求可能被代理拦截，出现误判。

### 2. 端口占用

若本机 `8000` 或 `5173` 已被占用，可切换临时端口，但要同步更新：

- 后端启动端口
- 前端 `VITE_API_BASE_URL`
- 后端 `CORS_ALLOW_ORIGINS`

## 回归检查

每完成一个大步骤后，至少回归：

1. 登录页是否仍可用
2. 聊天页是否仍可用
3. WebSocket 是否仍可连接
4. Alembic 迁移是否仍可执行
5. 工作流预览是否仍可生成与确认
6. 工作流执行是否仍可启动并完成
7. 错误恢复等待态是否仍可通过 `resume / redirect` 继续推进
8. 项目级记忆文件与响应字段是否仍可更新
9. 文档是否仍与实现一致
