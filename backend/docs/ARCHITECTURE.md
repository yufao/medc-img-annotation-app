# 系统架构概览 (Phase3 Skeleton)

> 本文档为后续演进（错误统一、多选标注、测试体系、云迁移）提供结构支撑；当前为骨架，随实现同步更新。

## 1. 总体结构

前后端分离：
- frontend (React + Vite)：组件化拆分后（Login / DatasetSelect / Annotate / 等）
- backend (Flask + MongoDB)：Blueprint + Service 分层

目录关键层次（backend/app）：
```
api/            # 蓝图 (Controller) 仅做参数与响应包装
core/           # 基础设施（数据库连接等）
services/       # 领域服务（dataset / label / image / annotation / export / user）
static/         # 静态文件（图片等）
user_config.py  # 用户/角色配置（后续可迁移数据库或 JWT）
routes.py       # legacy (已弃用; 将在清理阶段移除)
```

## 2. 分层职责
| 层 | 主要文件 | 职责 | 不包含 |
|----|---------|------|--------|
| API (Controller) | api/*.py | 参数解析、权限初步校验、调用 service | 业务规则、数据拼装细节 |
| Service | services/*.py | 业务逻辑、跨集合聚合、数据规范化、导出构建 | Web/HTTP 细节、权限判断（除必要守卫） |
| Core | core/db.py | 连接管理、未来可插入缓存/指标 | 业务逻辑 |
| Config | config.py / user_config.py | 系统 & 用户角色配置 | 运行态数据 |

## 3. 数据模型 (Mongo 集合)
- datasets: { id, name, description, image_count, status, created_at, multi_select }
- images: { image_id, image_path }
- image_datasets: { image_id, dataset_id }
- annotations: { record_id, dataset_id, image_id, expert_id, label_id, tip, datetime }
- labels: { label_id, label_name, category, dataset_id? }
- sequences: { _id: <seq_name>, sequence_value }
- users (暂无集合，使用 user_config 常量)

## 4. 新增字段：multi_select
| 字段 | 位置 | 类型 | 默认 | 含义 |
|------|------|------|------|------|
| multi_select | datasets | bool | false | 是否允许同一图片拥有多个标签（后续扩展 annotation 存储策略） |

迁移策略：
1. 新创建数据集写入该字段（缺省 False）。
2. 读取旧数据集时若缺失字段，列表响应自动补充 `multi_select: false`。
3. 允许 PATCH 更新（管理员）。
4. 多选模式实现阶段 1：后端允许一张图存在多个 annotation 记录（同 expert_id 不去重）。
5. 后续若需要 UI 支持多选 → 前端在标注面板允许选多个 label 并批量提交。

## 5. 标注策略（单选 vs 多选）
当前（单选）逻辑：同 (dataset_id, image_id, expert_id) upsert -> 保留一条记录。
多选模式（规划）：允许传入 label_id 列表，产生/更新多条记录；更新 endpoint 需要区分新增 & 删除。
本阶段仅落地数据集层字段与兼容读取，不改动 annotation 行为（避免一次性风险）。

## 6. 错误与响应（Phase4 计划）
目标：统一格式 `{ "success": true/false, "data": ..., "error": { code, message } }`
步骤：
1. 定义 ApiResponse 工具 & 自定义异常（DomainError / PermissionError / NotFoundError）。
2. Flask 全局 errorhandler 捕获并转化。
3. 渐进迁移各蓝图；保持兼容模式（添加 acceptLegacy=true? 暂不需要）。

## 7. 测试策略
| 层 | 测试类型 | 覆盖点 |
|----|----------|--------|
| Service | 单元 | dataset create/update/multi_select、annotation save/next、export sheet 生成 |
| API | 集成 | 权限码 403、分页、上传、导出下载 |
| 端到端(E2E) | 轻量脚本 | 核心流：创建 → 上传 → 标注 → 导出 |

工具：pytest + coverage；后续引入 Github Actions / 手动 pipeline。

## 8. 云部署简述（详见 MIGRATION.md 计划）
基础：Python 3.11+, Mongo 6.x、Nginx 前置（静态 + 反向代理），可选容器 Compose/单机。
关键点：环境变量 (.env)、日志轮转、数据备份（mongodump + cron）。

## 9. 逐步清理 Legacy
- routes.py 打标签 deprecated（已不再注册或设环境变量控制）
- 保留两周观察窗口后删除或移动到 docs/legacy/

## 10. 后续演进路线图
1. Phase3 完成：multi_select 字段、文档骨架、基础测试
2. Phase4：统一错误 / 云迁移文档 / CI / 性能指标
3. Phase5（规划）：前端多选 UI + 状态管理优化（Zustand/Jotai）+ 缓存层（可选 Redis）

---
更新时间：初始创建
