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
5. 文档是否仍与实现一致
