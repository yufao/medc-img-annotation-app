# 医学图像标注系统 (Medical Image Annotation System)

基于 Flask + React 的医学图像标注系统，支持按角色（admin/doctor/student）进行独立标注进度统计与管理。

## 🎯 项目概述

- 多角色：管理员、医生、学生
- 标注流程：获取下一张待标注图片、选择标签、备注并提交、自动跳到下一张
- 数据集管理：数据集、标签、图片上传与进度统计
- 导出：按数据集和用户筛选导出 Excel

提示：当前后端依赖 MongoDB。若数据库不可用，部分接口会不可用（有少量内存回退仅用于应急），建议务必配置 MongoDB 以获得完整功能。

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- MongoDB 4.0+

### 启动后端
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env .env.local 2>/dev/null || true  # 如无 .env 请自行创建
python3 run.py
```

### 启动前端（新终端）
```bash
cd frontend
npm install
./start_frontend.sh
```

### 访问
- 前端: http://localhost:3000
- 后端: http://localhost:5000
- 静态图片: 由后端提供 `/static/img/...`
- 测试账户: admin/admin123、doctor/doctor123、student/student123

## 🏗️ 结构

```
medc-img-annotation-app/
├── backend/
│   ├── app/
│   │   ├── routes.py           # 后端所有 API 路由
│   │   └── static/img/         # 图片目录（由上传或手动放置）
│   ├── config.py               # 配置（读取 .env）
│   ├── requirements.txt
│   ├── run.py                  # 启动入口
│   └── run_test.sh             # 简化启动脚本
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # 前端主功能与标注逻辑
│   │   └── main.jsx
│   ├── vite.config.js          # 代理到后端 5000 端口
│   └── start_frontend.sh
├── docker-compose.yml          # 可选
├── LOCAL_TEST_GUIDE.md         # 本地运行与排错指南
└── README.md
```

## 🔌 主要 API（与当前代码一致）

- 登录/用户
  - POST `/api/login`
- 数据集与统计
  - GET `/api/datasets`
  - GET `/api/datasets/{id}/statistics`
  - GET `/api/datasets/{id}/images`（备用列表接口）
- 标签
  - GET `/api/labels`（支持 dataset_id）
  - 管理标签：
    - POST `/api/admin/datasets/{id}/labels`
    - GET `/api/admin/datasets/{id}/labels`
    - PUT `/api/admin/datasets/{id}/labels`
- 图片与标注
  - POST `/api/images_with_annotations`（支持 include_all, 分页）
  - POST `/api/next_image`（按角色返回下一张未标注）
  - POST `/api/prev_image`
  - POST `/api/annotate`（新增/更新，自动处理 record_id）
  - POST `/api/update_annotation`（显式修改）
  - GET `/api/export`（支持按数据集、用户筛选导出 Excel）
- 管理数据集
  - POST `/api/admin/datasets`
  - DELETE `/api/admin/datasets/{id}`
  - POST `/api/admin/datasets/{id}/images`（上传图片）
  - POST `/api/admin/datasets/{id}/recount`（重算图片数）

## 🧭 前端标注流程说明（关键逻辑）

- 入口组件：`frontend/src/App.jsx` 的 `Annotate`
- 获取图片：
  1) 若从图片选择器带回 image_id，则精确加载该图及其标注
  2) 否则：
     - 调用 `/images_with_annotations`，优先选择“第一张未标注”
     - 若都已标注，则通过统计 `/datasets/{id}/statistics` 再次确认
     - 若统计显示未完成但无未标注记录，回退 `/next_image` 获取下一张
     - 仍无返回则视为全部完成
- 提交后：重复上述“优先未标注”的取图逻辑，避免误判“标注完成”。

2025-08-16 修复：当未携带指定 image_id 返回时，以“未标注优先”作为首要策略，并通过统计+next_image 双重校验，解决明明存在未标注图片却误提示“标注完成”的问题。

## 🔧 环境变量（后端）

`.env` 示例：
```env
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=medical_annotation
UPLOAD_FOLDER=app/static/img
MAX_CONTENT_LENGTH=16777216
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SECRET_KEY=changeme
JWT_SECRET_KEY=changeme
```

## 🧪 简单验证

1) 登录 -> 选择数据集 -> 标注若干图片 -> 查看进度环
2) 导出 Excel（可按 dataset_id/expert_id 过滤）

## � 变更日志（摘要）

- 2025-08-16：修复前端取图逻辑，优先未标注 + 统计/next_image 双重校验；补充文档与注释

---

仅供教学与研究使用，不得用于临床诊断。
