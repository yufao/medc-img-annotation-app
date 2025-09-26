# 设计与规划（API / 工具 / 功能）

本文件阐述后端 API、工具脚本与前端关键功能的设计思路与取舍，并给出迭代规划。

## 后端 API 设计

- 分层：Controller(BluePrint) -> Service -> Repository -> Core(DB)
- 统一响应：逐步迁移到 `app/api/response.py` 提供的 `{ code, message, data }` 格式
- 向后兼容：在迁移期间保留 legacy 字段 `{ msg:"success" }`
- 身份：短期内沿用配置用户；长期引入 JWT（`/login` 发 token，后续端点鉴权）
- 多选标注：`datasets.multi_select` 字段驱动行为
  - V1：仅数据结构与读取兼容（已落地字段），标注仍单选
  - V2：在 `POST /api/annotate` 支持 `label` 列表；新增 `DELETE /api/annotation` 删除某一 label

约束与规范：
- 所有管理员端点必须显式 `role=admin`
- 分页统一 `page/pageSize`，默认 `1/20`
- 错误使用 `ApiError` 抛出，由 `register_error_handlers` 统一处理

## 服务与仓储

- dataset_service：提供列表、统计、创建、删除、recount 与 `multi_select` 更新；内部有 15s 统计缓存
- image_service：批量上传、列表（合并标注与标签名称）
- annotation_service：上一张/下一张、合并列表、保存/更新标注
- label_service：按数据集维护标签（覆盖更新）
- repository：优先从 `dataset_repository` 开始，后续将其它集合统一迁移至仓储抽象，便于测试与替换

## 数据库

- 集合与索引：
  - annotations: 建议索引 `(dataset_id, expert_id, image_id)` 与 `(dataset_id, image_id)`
  - image_datasets: 建议索引 `(dataset_id)` 与 `(image_id)`
  - sequences: `_id` 唯一
- 迁移策略：脚本 `migrate_db.py` 支持 dry-run；变更字段以兼容读取为先

## 前端关键功能设计

- 标注流程：优先“未标注” -> 统计校验 -> next_image 回退；提交后重复上述以避免误判
- 组件拆分：`components/annotation/*` 与 `components/admin/*`
- API 客户端：`src/api/client.js` 集中封装基础 URL 与错误处理
- 状态：当前使用 hooks，本阶段不强引入全局状态库；若多选上线可考虑 Zustand

## 工具脚本

- manage.sh：单入口；创建目录、生成 .env、构建与运行 Compose、日志与清理
- deploy/deploy.sh：CI/CD 占位，默认调用 manage.sh build+restart
- backend 脚本：migrate/setup/db_utils；保持幂等

## 路线图

- Phase 3（当前）
  - 文档体系完善（本次）
  - API 参考与工具手册（本次）
  - routes.py 保留并标注兼容（已完成）
- Phase 4
  - 统一响应落地到所有蓝图
  - 补充单元/集成测试与最小 CI
  - Docker 镜像与离线包规范
- Phase 5
  - 多选标注 API + 前端 UI
  - 用户认证 JWT 化、权限中间件
