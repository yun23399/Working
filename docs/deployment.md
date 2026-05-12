# 部署说明

本文档描述项目从本地开发到后续部署的建议路径。

## 1. 当前阶段定位

当前优先目标是本地开发环境跑通，不直接进入生产部署。

建议阶段：

1. 本地单机开发
2. 本地或测试机部署
3. 后续再考虑生产化

## 2. 本地开发环境

### 前端

- Node.js 18+
- npm 9+

### 后端

- Python 3.11+
- SQLite

## 3. 本地运行建议

前端：

```powershell
cd frontend
npm install
npm run dev
```

后端：

```powershell
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 4. 生产化前必须补齐的内容

- PostgreSQL 支持
- Docker 化部署
- 日志轮转与保留策略
- 机密配置管理
- 健康检查
- 备份策略
- 监控与告警

## 5. 数据库建议

- 阶段一、二使用 SQLite 即可
- 阶段五切换 PostgreSQL

## 6. 日志建议

- 开发环境输出到控制台和本地 `logs/`
- 生产环境建议集中式采集

## 7. GitHub 与交付建议

- 所有本地阶段性成果应提交到 GitHub 远程仓库
- 默认开发分支使用 `dev`
- `main` 仅用于稳定版本
- 建议在 GitHub 上启用 PR 审查与 CI
