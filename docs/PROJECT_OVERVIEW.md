# 项目总体说明（结构与职责）

本项目为医学图像标注系统，采用前后端分离：后端 Flask + MongoDB，前端 React + Vite。提供容器化与脚本化的本地/生产部署方案。

## 顶层结构

```
medc-img-annotation-app/
├── backend/                # Flask 后端（API、服务层、数据库）
│   ├── app/                # 业务代码（api/ services/ core/ 等）
│   ├── docs/               # 后端文档（架构/数据库/部署/回归清单）
│   ├── requirements.txt    # Python 依赖
│   └── run.py              # 开发模式入口（Flask 内置）
├── frontend/               # React 前端（Vite）
│   ├── src/                # 组件、路由、状态
│   ├── Dockerfile          # 前端镜像构建
│   └── README.md           # 前端说明
├── deploy/                 # 部署相关（系统服务、脚本与说明）
├── manage.sh               # 顶层管理脚本（启动/停止/构建/打包）
├── docker-compose*.yml     # 开发/生产的 Compose 配置
├── static/                 # 运行时静态资源（如迁移的图片）
└── docs/                   # 本目录：项目总览、API、工具脚本等说明
```

## 后端分层

- app/api: HTTP 层（Blueprint）。只做参数校验/响应包装，调用服务层
- app/services: 领域服务，封装核心业务逻辑与跨集合聚合
- app/core: 基础设施（Mongo 连接、健康检查等）
- app/repositories: 数据持久化抽象（当前仅数据集部分）
- app/static: 静态文件（开发模式下图片路径）

关键入口：`backend/run.py`（开发）与 `gunicorn`（生产，见 `backend/docs/DEPLOYMENT.md`）。

## 前端结构

- src/components/annotation: 标注工作流组件（取图、提交、导出）
- src/components/admin: 数据集管理
- src/api/client.js: API 客户端封装（与后端端点对应）

## 数据库

- MongoDB，集合包括：datasets / images / image_datasets / annotations / labels / sequences
- 连接配置见 `.env` 与 `backend/app/core/db.py`，指南见 `backend/docs/DB_GUIDE.md`

## 运行方式

- 开发：`./manage.sh dev`（或 `backend/python run.py` + `frontend/npm run dev`）
- 生产：`./manage.sh start`（Compose）或 `gunicorn`（详见部署文档）

## 文档导航

- 架构：`backend/docs/ARCHITECTURE.md`
- 数据库：`backend/docs/DB_GUIDE.md`
- 部署：`backend/docs/DEPLOYMENT.md`（后端）与 `deploy/DEPLOY_GUIDE.md`
- API：`docs/backend/API_REFERENCE.md`
- 回归清单：`backend/docs/REGRESSION_CHECKLIST.md`
