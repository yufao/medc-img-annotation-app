# 医学图像标注系统 (Medical Image Annotation System)

基于 Flask + React 的医学图像标注系统，支持按角色（admin/doctor/student）进行独立标注进度统计与管理。

## 🎯 项目概述

- **多角色管理**：管理员、医生、学生三种角色
- **标注流程**：获取下一张待标注图片、选择标签、备注并提交、自动跳到下一张
- **数据集管理**：数据集、标签、图片上传与进度统计
- **数据导出**：按数据集和用户筛选导出 Excel

## 🚀 快速启动

### 方式一：一键启动（推荐）
```bash
# 启动生产环境
./manage.sh start

# 启动开发环境
./manage.sh dev

# 查看帮助
./manage.sh help
```

### 方式二：手动启动
```bash
# 启动后端
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 run.py

# 启动前端（新终端）
cd frontend
npm install
npm run dev
```

## 📦 Docker 部署

### 本地部署
```bash
# 构建并启动
./manage.sh build
./manage.sh start

# 查看状态
./manage.sh status

# 查看日志
./manage.sh logs
```

### 创建部署包
```bash
# 创建部署包
./manage.sh package

# 选择类型：
# 1. 在线部署包（需要网络下载镜像）
# 2. 离线部署包（包含所有镜像文件）
```

## 📁 项目结构

```
medc-img-annotation-app/
├── backend/                    # Flask 后端
│   ├── app/                   
│   │   ├── routes.py          # API 路由
│   │   ├── models.py          # 数据模型
│   │   └── static/            # 静态文件
│   ├── requirements.txt       # 依赖包
│   └── run.py                 # 启动文件
├── frontend/                  # React 前端
│   ├── src/                   # 源码
│   ├── public/                # 公共资源
│   └── package.json           # 依赖配置
├── docker-compose.yml         # 开发环境配置
├── docker-compose.prod.yml    # 生产环境配置
├── manage.sh                  # 统一管理脚本
└── README.md                  # 项目说明
```

## 🔧 管理命令

```bash
./manage.sh start          # 启动生产环境
./manage.sh dev            # 启动开发环境
./manage.sh stop           # 停止服务
./manage.sh restart        # 重启服务
./manage.sh status         # 查看状态
./manage.sh logs           # 查看日志
./manage.sh build          # 构建镜像
./manage.sh test           # 运行测试
./manage.sh package        # 创建部署包
./manage.sh clean          # 清理环境
./manage.sh setup          # 初始化环境
```

## 🌐 访问信息

- **前端界面**: http://localhost
- **后端API**: http://localhost:5000

### 默认账户
- **管理员**: admin/admin123
- **医生**: doctor/doctor123  
- **学生**: student/student123

## 📋 环境要求

- Docker 20.10+
- Docker Compose 1.29+
- 或者：Python 3.8+ + Node.js 16+ + MongoDB 4.0+

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

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
