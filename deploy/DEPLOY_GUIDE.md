# 部署总览（整仓）

本指南承接 `backend/docs/DEPLOYMENT.md`，补充前端与 Compose 的一体化部署流程。

## 先决条件
- Docker 20.10+、Docker Compose 2.x
- 或者：Python 3.10+、Node.js 18+、MongoDB 6.x

## 一键流程（推荐）
```bash
./manage.sh setup
./manage.sh build   # 构建镜像
./manage.sh start   # 启动生产
./manage.sh status
```

访问：
- 前端 http://localhost
- 后端 http://localhost:5000

## 开发环境
```bash
./manage.sh dev
```
说明：将以前端/后端开发镜像运行，支持热更新。

## 环境变量
- 后端 `.env` 位于 `backend/.env`，样例见 `backend/.env.example`
- 关键项：`MONGO_URI`/`MONGO_DB`（或兼容变量 `MONGODB_URI`/`MONGODB_DB`）

## 升级与回滚
- 升级：`git pull && ./manage.sh build && ./manage.sh restart`
- 回滚：保留上一个镜像标签或使用离线包复原

## 日志与排障
- Compose 日志：`./manage.sh logs`
- 健康检查：`GET /api/healthz` -> `{ ok, db_connected }`
- DB 状态：`GET /api/admin/db_status?role=admin`

## 安全要点
- 生产环境务必使用强 `SECRET_KEY/JWT_SECRET_KEY`
- Mongo 设置用户最小权限；开启备份与索引
- 前端 Nginx 可配置静态缓存与反向代理（见 `frontend/nginx.conf`）