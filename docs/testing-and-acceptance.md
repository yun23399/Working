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
21. 代码执行工具与真实产物回传链路可用
22. 文件工具与真实文本产物回传链路可用
23. 外部 API 工具与真实响应产物回传链路可用
24. 浏览器工具与真实截图/页面元数据回传链路可用
25. 图像工具与真实图片/图像元数据回传链路可用
26. 工作流产物预览与受保护文件读取链路可用
27. 本地多项目管理与对话迁移链路可用
28. 当前对话内搜索链路可用
29. 用户自定义 Agent 角色模板链路可用
30. Agent 配置导入/导出链路可用
31. 并发工作流上限配置链路可用
32. 工作流运行日志文件回填与分级过滤链路可用
33. 页面过渡动效优化链路可用
34. 本地插件自动加载、启停与工作流选角接入链路可用

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
- 重新进入当前工作流后，前端会通过 `/api/workflows/{conversation_id}/{workflow_id}/runtime-logs` 回填最近运行日志
- 日志面板支持 `DEBUG / INFO / WARNING / ERROR` 分级过滤、关键词搜索与导出当前筛选结果

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

### 用例 14：阶段三代码执行工具链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- 2026-05-13 实测通过：`POST /api/workflows/{conversation_id}/{workflow_id}/execute` 完成后，`workspace.artifacts` 可返回
  `backend_plan.json` 和 `code_execution_result.json`
- 2026-05-13 实测通过：真实文件已落盘到
  `workspace/projects/conversation_38/workflow_38/artifacts/`
- `execution_logs[].artifacts` 会同步记录当前节点真实产物路径

### 用例 15：阶段三文件工具链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- 2026-05-13 实测通过：`conversation_40 / workflow_40` 执行完成后，`workspace.artifacts` 返回
  `pm_summary.md`、`backend_summary.md`、`backend_plan.json` 与 `code_execution_result.json`
- 2026-05-13 实测通过：真实文件已落盘到
  `workspace/projects/conversation_40/workflow_40/artifacts/`
- `execution_logs[].artifacts` 与磁盘目录内容一致，可区分文本摘要产物与代码执行产物

### 用例 16：阶段三外部 API 工具链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- 2026-05-13 实测通过：`conversation_41 / workflow_41` 执行完成后，`workspace.artifacts` 返回
  `api_response.json`、`pm_summary.md`、`backend_summary.md`、`backend_plan.json` 与 `code_execution_result.json`
- 2026-05-13 实测通过：`api_response.json` 已落盘到
  `workspace/projects/conversation_41/workflow_41/artifacts/`
- `api_response.json` 内包含请求地址 `http://127.0.0.1:8000/health`、状态码 `200` 与响应体

### 用例 17：阶段三浏览器工具链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- 2026-05-13 工具级实测通过：`BrowserTool.execute()` 可访问 `http://127.0.0.1:5173/login`
- 2026-05-13 Agent 级实测通过：前端模板可回传 `browser_snapshot.png` 与 `browser_result.json`
- 2026-05-13 工作流级实测通过：`conversation_48 / workflow_47` 执行完成后，`workspace.artifacts` 返回
  `frontend_snapshot.png`、`frontend_browser_result.json`、`qa_snapshot.png` 与 `qa_browser_result.json`
- 真实文件已落盘到
  `workspace/projects/conversation_48/workflow_47/artifacts/`
- `frontend_browser_result.json` 与 `qa_browser_result.json` 内包含访问地址、页面标题 `AgentFlow` 与状态码 `200`

### 用例 18：阶段三图像工具链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- 2026-05-13 工具级实测通过：`ImageTool.execute()` 可生成 `manual_design_mockup.png` 与 `manual_design_result.json`
- 2026-05-13 Agent 级实测通过：设计师模板可回传图片产物与图像结果文件
- 2026-05-13 工作流级实测通过：`conversation_50 / workflow_48` 执行完成后，`workspace.artifacts` 返回
  `design_brief.md`、`design_mockup.png` 与 `design_image_result.json`
- 真实文件已落盘到
  `workspace/projects/conversation_50/workflow_48/artifacts/`
- 当前环境未配置 `OPENAI_API_KEY`，因此 `design_image_result.json` 记录为 `local_placeholder_renderer` 回退路径，用于保证链路可验证

### 用例 19：阶段三工作流产物预览链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- 2026-05-13 接口实测通过：`GET /api/workflows/50/48/artifacts` 返回 `200`，当前工作流可见产物共 `12` 项
- 2026-05-13 接口实测通过：`GET /api/workflows/50/48/artifacts/file?path=design_mockup.png` 返回 `200`，`content-type=image/png`
- 2026-05-13 接口实测通过：`GET /api/workflows/50/48/artifacts/file?path=design_brief.md` 返回 `200`，`content-type=text/markdown`
- 2026-05-13 接口实测通过：不存在或无权限的会话访问会返回 `404`，错误码 `CONVERSATION_NOT_FOUND`
- 聊天页新增产物预览面板，当前可按真实文件类型切换代码、文档与图片预览

### 用例 20：阶段三工作流产物导出链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- 2026-05-13 接口实测通过：`GET /api/workflows/51/49/artifacts/export` 返回 `200`
- 2026-05-13 接口实测通过：响应头 `content-disposition=attachment; filename=\"workflow_49_artifacts.zip\"`
- 2026-05-13 接口实测通过：压缩包内文件列表为 `plan.json`、`summary.md`
- 聊天页产物面板新增“导出产物”按钮，可直接下载当前工作流全部真实产物

### 用例 21：阶段三 Token 用量展示链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- 聊天头部的 Token 统计已抽离为独立 `TokenCounter` 组件
- 当前统计口径保持不变，仍按 `messages[].tokenCount` 汇总显示本次会话累计 Token 数

### 用例 22：阶段四本地通知链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- 2026-05-13 代码级实测通过：`SystemNotifier.notify()` 调用后，会在仓库根目录生成 `logs/notifications.log`
- 2026-05-13 代码级实测通过：通知日志路径固定为仓库根目录 `logs/`，不会漂移到 `backend/logs/`
- 当前桌面通知采用 Windows PowerShell 气泡提醒，若环境不支持会自动回退到日志记录，不影响工作流执行
- 若 PowerShell 控制台未切换到 UTF-8，直接 `Get-Content` 查看中文通知文本可能显示为问号；文件实际写入仍为 UTF-8

### 用例 23：阶段四本地多项目管理链路

验证结果：

- `npm run lint` 通过
- `npm run build` 通过
- 项目页支持按项目名称或摘要搜索当前本地项目
- 项目页支持创建、编辑和删除本地项目分组
- 删除项目时会自动把该项目下对话转移到当前项目或首个可用项目
- 项目页支持选中某条对话并迁移到其他项目
- 从项目页打开指定对话后，聊天页会保留该项目上下文，不会回退到当前项目下的首条对话

### 用例 24：阶段四当前对话内搜索链路

验证结果：

- `npm run lint` 通过
- `npm run build` 通过
- 聊天页支持在当前对话内输入关键词搜索消息
- 匹配消息会高亮关键词片段，并区分当前焦点结果
- 可通过上下切换按钮在匹配结果之间跳转定位
- 切换到另一条对话后，上一条对话的搜索关键词与焦点状态会自动清空

### 用例 25：阶段四用户自定义 Agent 角色模板链路

验证结果：

- `python -m alembic upgrade head` 通过
- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- 设置页支持创建、编辑、启停和删除自定义角色模板
- 自定义角色模板支持配置触发关键词、系统提示词、工具集和最大重试次数
- 重新规划工作流后，命中关键词的自定义角色会以 `template_source=custom` 进入节点列表
- 工作流卡片可展示节点来源为“自定义角色”

### 用例 26：阶段四 Agent 配置导入/导出链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- `GET /api/agent-role-templates/export` 可返回当前账号的角色模板 JSON 配置包
- `POST /api/agent-role-templates/import` 支持 `skip` 和 `overwrite` 两种冲突处理策略
- 2026-05-13 API 级实测通过：导入跳过策略会保留同名现有模板，并创建新的非冲突模板
- 2026-05-13 API 级实测通过：导入覆盖策略会更新同名模板的摘要、工具、启停状态与重试次数
- 设置页已新增“导出模板”和“导入模板”入口，并可回显逐条导入结果

### 用例 27：阶段四并发工作流上限配置链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- 设置页已新增“工作流并发上限”面板，可展示当前上限、执行中数量、剩余槽位与是否已满
- `GET /api/system-settings/runtime` 可返回当前运行时并发快照
- `PUT /api/system-settings/runtime` 可更新 `MAX_CONCURRENT_WORKFLOWS` 并立即返回最新快照
- `POST /api/workflows/{conversation_id}/{workflow_id}/execute` 已接入并发槽位校验，超限时返回 `409`
- 超限错误码为 `WORKFLOW_CONCURRENCY_LIMIT_REACHED`
- 当前并发控制为单进程内存级实现，适用于本地单实例联调

### 用例 28：阶段四日志面板文件回填与分级过滤链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- 2026-05-13 运行级实测通过：执行工作流后，`GET /api/workflows/{conversation_id}/{workflow_id}/runtime-logs` 返回最近结构化日志记录
- 2026-05-13 文件级实测通过：共享工作区 `context/runtime_logs.jsonl` 已真实落盘
- 聊天页进入当前工作流后，可回填历史日志并继续接收 WebSocket 增量日志
- `LogViewer` 已支持按等级筛选、关键词搜索、时间戳展示和导出 `workflow-runtime-logs.txt`

### 用例 29：阶段四页面过渡动效优化链路

验证结果：

- `npm run lint` 通过
- `npm run build` 通过
- `AppRouter` 已接入 `AnimatePresence`
- 登录页、聊天页、项目页与设置页统一通过 `PageTransition` 承载路由切换动效
- 默认环境下页面切换时会呈现轻微上移、淡入与顶部冷蓝光晕过渡
- 若浏览器或系统开启“减少动态效果”，页面动效会自动降级为更轻的透明度过渡

### 用例 30：阶段五插件机制链路

验证结果：

- `python -m ruff check .` 通过
- `python -m black --check .` 通过
- `npm run lint` 通过
- `npm run build` 通过
- `GET /api/system-settings/plugins` 可返回当前本地插件列表与插件模板摘要
- `PUT /api/system-settings/plugins/{plugin_id}` 可更新指定插件启停状态，并写回根目录 `.env`
- 重新规划工作流后，命中插件关键词的节点会以 `template_source=plugin` 进入节点列表
- 示例插件 `plugins/examples/research_helper` 可作为本地插件开发参考

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
9. `workspace.artifacts` 是否仍能返回真实产物文件
10. `file_tool` 生成的 `.md` 产物是否仍能进入节点 artifacts
11. `api_caller` 生成的 `api_response.json` 是否仍能进入节点 artifacts
12. `browser_tool` 生成的截图与元数据是否仍能进入节点 artifacts
13. `image_tool` 生成的图片与元数据是否仍能进入节点 artifacts
14. `/api/workflows/{conversation_id}/{workflow_id}/artifacts` 是否仍能返回真实产物清单
15. `/api/workflows/{conversation_id}/{workflow_id}/artifacts/file` 是否仍能正确返回图片或文本内容
16. 本地项目创建、编辑、删除与对话迁移是否仍可用
17. 当前对话内搜索、高亮与跳转是否仍可用
18. 自定义角色模板的增删改查与重新规划接入是否仍可用
19. 角色模板导入/导出与导入结果回显是否仍可用
20. `GET /api/system-settings/runtime` 与 `PUT /api/system-settings/runtime` 是否仍可用
21. 工作流执行超限时是否仍返回 `WORKFLOW_CONCURRENCY_LIMIT_REACHED`
22. `/api/workflows/{conversation_id}/{workflow_id}/runtime-logs` 是否仍可返回最近运行日志
23. `LogViewer` 的分级过滤、关键词搜索与导出是否仍可用
24. 登录页、聊天页、项目页与设置页切换时的页面转场是否仍可用
25. 本地插件列表、启停控制与设置页展示是否仍可用
26. 重新规划工作流后，插件模板是否仍可按关键词命中并返回 `template_source=plugin`
27. 文档是否仍与实现一致

### ?? 31????????? API ????

?????

- `GET /api/system-settings/llm` ????????????????????
- `PUT /api/system-settings/llm` ?????? `.env` ?????
- `POST /api/system-settings/llm/test` ???????? OpenAI ???????
- ?????? `/api/conversations/{conversation_id}/manager-state` ??????????????
- ?????????`POST /api/conversations/{conversation_id}/start-task` ??????? `status=confirmed` ?????
- 2026-05-13 ??????? `https://shiyunapi.com/v1` + `gpt-5.4` ???????????????
