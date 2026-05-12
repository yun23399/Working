# 测试与验收文档

## 阶段一验收目标

阶段一不是“文件创建完成”，而是“最小闭环跑通”。

需要验证以下链路：

1. 前端依赖安装成功
2. 前端 lint 通过
3. 前端 build 通过
4. 后端依赖安装成功
5. 后端 ruff 通过
6. 后端 black 检查通过
7. 数据库迁移成功
8. 后端服务可启动
9. 注册登录可用
10. 对话接口可用
11. WebSocket 流式消息可用
12. 历史消息持久化可用

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
uvicorn app.main:app --reload
```

## 最小联调用例

### 用例 1：注册与登录

预期：

- 用户可成功注册
- 用户可成功登录
- 返回 JWT

### 用例 2：创建项目与对话

预期：

- 用户可创建项目
- 用户可创建对话
- 列表接口可返回新创建数据

### 用例 3：聊天流式回复

预期：

- 发送消息成功
- 前端收到 WebSocket `token`
- 前端显示打字机效果
- 流式完成后消息被持久化

## 阶段二验收目标

- Manager 能生成工作流
- 用户可确认工作流
- Agent 状态可视化
- 日志与产出物可实时查看

## 回归检查

每完成一个大步骤后应回归：

1. 登录页是否仍可用
2. 聊天页是否仍可用
3. WebSocket 是否仍可连接
4. 数据库迁移是否仍可执行
5. 关键文档是否仍与实现一致
