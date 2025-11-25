# 工具与脚本使用说明

本项目提供统一管理脚本与后端辅助脚本，便于开发、测试与部署。

## 1. 顶层管理脚本 (`manage.sh`)

位于项目根目录，是日常运维的主要入口。

- **开发模式**：`./manage.sh dev` (启动后端与前端开发服务器)
- **生产启动**：`./manage.sh start` (使用 Gunicorn 启动后端)
- **构建镜像**：`./manage.sh build`
- **查看状态**：`./manage.sh status`
- **查看日志**：`./manage.sh logs`
- **打包发布**：`./manage.sh package` (生成在线/离线部署包)
- **环境清理**：`./manage.sh clean` (清理临时文件)
- **初始化**：`./manage.sh setup` (创建目录、生成 .env)

## 2. 数据库维护工具 (`backend/`)

位于 `backend/` 目录下，用于数据库初始化、迁移与修复。

### 2.1 标签修复工具 (`fix_labels_database.py`)
**功能**：修复历史数据中未关联数据集 ID (`dataset_id`) 的标签。
**适用场景**：
- 从旧版本升级后，发现标签无法在特定数据集中显示。
- 数据库中存在“孤立”标签。

**使用方法**：
```bash
cd backend
python fix_labels_database.py
```
**交互模式**：
- 脚本会分析当前标签状态。
- 提供交互式菜单，可选择将孤立标签分配给指定数据集，或批量处理。

### 2.2 数据库初始化 (`setup_database.py`)
**功能**：初始化数据库，创建示例用户与数据集。
**注意**：默认会重置部分集合，生产环境慎用。

### 2.3 数据迁移工具 (`migrate_db.py`)
**功能**：将数据从旧数据库迁移到新数据库结构。
**参数**：
- `--src-db`: 源数据库名
- `--dst-db`: 目标数据库名
- `--dry-run`: 试运行（不写入）

### 2.4 数据库工具库 (`db_utils.py`)
包含序列号生成、索引创建等底层工具函数。

## 3. 测试脚本

- `backend/run_test.sh`: 运行后端所有测试。
- `backend/tests/`: 存放 pytest 测试用例。

## 4. 部署相关 (`deploy/`)

- `deploy/PROD_UPDATE_NO_DOCKER.md`: 非 Docker 环境生产更新指南。
- `deploy/DEPLOY_GUIDE.md`: 通用部署指南。

## 5. 管理员功能 (UI)

虽然不是脚本文件，但以下功能属于管理工具范畴：

- **清理标注 (Clear Annotations)**:
  - 位置：`Admin` -> `Dataset Management` -> `Clear Annotations` 按钮。
  - 功能：**永久删除**指定数据集下的所有标注记录（保留图片与数据集本身）。
  - 警告：此操作不可逆，请谨慎使用。

- **多标签支持 (Multi-label)**:
  - 位置：创建/编辑数据集时勾选 `Multi-select`。
  - 功能：允许单张图片选择多个标签。

