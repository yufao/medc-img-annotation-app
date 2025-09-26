# 工具与脚本使用说明

本项目提供统一管理脚本与后端辅助脚本，便于开发、测试与部署。

## 顶层管理脚本 manage.sh

- 开发：`./manage.sh dev`
- 生产启动：`./manage.sh start`
- 构建镜像：`./manage.sh build`
- 查看状态/日志：`./manage.sh status` / `./manage.sh logs`
- 打包：`./manage.sh package`（在线/离线）
- 清理：`./manage.sh clean`
- 初始化：`./manage.sh setup`

说明：脚本会创建 `data/ logs/ static/`，并为后端生成 `.env`（如不存在）。

## 后端脚本（backend/）

- `setup_database.py`：初始化示例数据（会重置集合）
- `migrate_db.py`：旧库 -> 新库数据迁移
- `db_utils.py`：序列修复等工具
- `run_test.sh`：运行内置测试脚本

示例：
```bash
cd backend
python migrate_db.py --src-db local --dst-db medc_annotation_dev --dry-run
python setup_database.py
```

## 部署目录 deploy/

- `DEPLOY_GUIDE.md`：部署指导（systemd/Gunicorn/Compose）
- `deploy.sh`：留作自动部署钩子（可按需填充）

更多细节见：
- `backend/docs/DEPLOYMENT.md`（后端运行模式与 systemd）
- `backend/docs/DB_GUIDE.md`（数据库配置）
