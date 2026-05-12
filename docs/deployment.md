# 部署说明

本文档描述项目当前的本地开发部署方式，以及后续进入测试环境和生产环境前需要补齐的事项。

## 1. 当前阶段定位

当前项目仍处于阶段一，本轮目标是保证：

1. 仓库从零拉取后可安装依赖
2. 数据库可通过 Alembic 初始化
3. 前后端可成功联调
4. 最小聊天闭环可运行

## 2. 本地开发环境要求

### 前端

- Node.js 18+
- npm 9+

### 后端

- Python 3.11+
- SQLite

## 3. 环境变量

后端关键变量：

```env
DATABASE_URL=sqlite:///./data/app.db
JWT_SECRET_KEY=
APP_HOST=127.0.0.1
APP_PORT=8000
CORS_ALLOW_ORIGINS=http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:5174,http://localhost:5174,http://127.0.0.1:4173,http://localhost:4173
```

前端关键变量：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 4. 本地启动建议

### 后端

```powershell
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 前端

```powershell
cd frontend
npm install
$env:VITE_API_BASE_URL='http://127.0.0.1:8000'
npm run dev
```

### 预览构建

```powershell
cd frontend
npm run build
npm run preview
```

## 5. 当前实现的部署边界

当前版本适合：

- 本地开发
- 本地验收
- 小范围测试环境联调

当前还不适合直接作为生产版本上线，因为以下能力尚未完成：

- 真实 LLM 流式输出
- 项目实体与工作流实体
- Docker 沙盒隔离
- PostgreSQL
- 统一监控与告警
- 静态资源与后端统一发布方案

## 6. 进入测试/生产前必须补齐

- 真实 LLM 适配层
- Docker 化部署
- 机密配置管理
- 统一日志采集
- 健康检查与重启策略
- 数据备份方案
- 生产数据库切换
- CI/CD 发布流程

## 7. GitHub 与交付建议

- 所有阶段性成果提交到 `origin/dev`
- 阶段稳定后再从 `dev` 合并到 `main`
- 每次推送前至少通过 lint、build、ruff、black、迁移验证
