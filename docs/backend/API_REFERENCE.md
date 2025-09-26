# 后端 API 参考（覆盖全项目）

本文档基于 `backend/app/api/*.py` 与 legacy `routes.py`，对外统一接口保持兼容。返回结构以现有实现为准（逐步向 `app/api/response.py` 统一）。

## 约定
- 基础路径：`/api/*`
- 成功：常见为 `{ msg: "success" }` 或 `{ code:"ok", message:"success", data: ... }`
- 错误：`403 权限不足`、`404 未找到`、`500 数据库连接不可用/内部错误`

## 认证
- POST `/api/login`
  - body: `{ username, password }`
  - 200: `{ msg: "success", role }`
  - 401: `{ msg: "fail" }`

## 数据集 datasets
- GET `/api/datasets`
  - 200: `[{ id, name, description, image_count, status, created_at, multi_select(false 默认) }]`
- GET `/api/datasets/{dataset_id}/statistics?expert_id={username}`
  - 200: `{ total_count, annotated_count }`

### 管理端 datasets（需 role=admin）
- POST `/api/admin/datasets`
  - body: `{ role:"admin", name, description?, multi_select? }`
  - 201: `{ code:"ok", data:{ dataset_id } }`
- PATCH `/api/admin/datasets/{id}/multi-select`
  - body: `{ role:"admin", multi_select: boolean }`
  - 200: `{ dataset_id, multi_select }`
- DELETE `/api/admin/datasets/{id}?role=admin`
  - 200: `{ deleted_images }`
- POST `/api/admin/datasets/{id}/recount`
  - body: `{ role:"admin" }`
  - 200: `{ dataset_id, image_count }`

## 标签 labels
- GET `/api/labels?dataset_id?`
  - 200: `[{ label_id, name, dataset_id? }]`
- 管理端
  - POST `/api/admin/datasets/{id}/labels` body: `{ role:"admin", labels:[{name,category?}, ...] }`
    - 201: `{ msg:"success", added_labels, labels:[{label_id,label_name,category,dataset_id}...] }`
  - GET `/api/admin/datasets/{id}/labels?role=admin`
    - 200: `[{ label_id,label_name,category,dataset_id }]`
  - PUT `/api/admin/datasets/{id}/labels` body: `{ role:"admin", labels:[...] }`
    - 200: `{ msg:"success", updated_labels: <count> }`

## 图片 images
- GET `/api/datasets/{id}/images?expert_id=&page=&pageSize=`
  - 200: `[{ image_id, filename, image_path, annotation? }]`
- 管理端上传 POST `/api/admin/datasets/{id}/images`
  - multipart form: `role=admin, images[]=...`
  - 201: `{ msg:"success", uploaded, failed, images:[{image_id,filename,original_name}], errors:[...] }`

## 标注 annotations
- POST `/api/images_with_annotations`
  - body: `{ dataset_id, expert_id, include_all(false), page(1), pageSize(20) }`
  - 200: `[{ image_id, filename, image_path, annotation? }]`
- POST `/api/prev_image` body: `{ dataset_id, image_id }`
  - 200: `{ image_id, filename, image_path? } | { msg:"no previous image" }`
- POST `/api/next_image` body: `{ dataset_id, expert_id }`
  - 200: `{ image_id, filename } | { msg:"done" }`
- POST `/api/annotate`
  - body: `{ dataset_id, image_id, expert_id, label, tip? }`
  - 200: `{ msg:"saved", expert_id }`
- POST `/api/update_annotation`
  - body: `{ dataset_id, image_id, expert_id, label, tip? }`
  - 200: `{ msg:"updated" } | { msg:"not found or not changed" }`

## 导出 export
- GET `/api/export?dataset_id=&expert_id=`
  - 200: 下载 Excel 文件（xlsx），文件名包含 dataset_id 与 expert_id 关键信息

## 管理与调试
- GET `/api/admin/users?role=admin`
  - 200: `[{ username, role, description }]`
- GET `/api/admin/users/config?role=admin`
  - 200: `{ message, config_file, instructions[], current_users_count, roles_mapping }`
- GET `/api/admin/db_status?role=admin`
  - 200: `{ connected, mongo_uri, db_name, collections? }`
- GET `/api/debug/db`
  - 200: `{ use_database_flag, mongo_uri, db_name, connected, collections? }`
- 健康检查 GET `/api/healthz`
  - 200: `{ ok: true, db_connected: boolean }`

## 错误码与响应
- 权限不足：`403 { msg:"error", error:"权限不足" }` 或 `{ code:"forbidden" }`
- 数据库不可用：`500 { msg:"error", error:"数据库连接不可用" }`
- 参数无效：`400 { msg:"error", error: "..." }` 或 `{ code:"invalid_param" }`

## 变更记录（摘要）
- 2025-08~09：将大路由拆分至 `app/api/*`；引入 `response.py` 统一响应骨架；datasets 新增 `multi_select` 字段
