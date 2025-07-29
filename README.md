# 医学图像标注系统 (Medical Image Annotation System) - 重构版本

一个基于 Web 的医学图像标注系统，支持多角色用户（放射科专家、实习医师、医学生）进行医学图像标注和数据管理。

**📋 重要说明: 本版本已完成重构，移除了本地测试时的数据库依赖，可使用Mock数据进行本地测试。**

## 🎯 项目概述

本系统旨在为医学教育和研究提供一个专业的图像标注平台，支持：

- **多角色用户管理**：放射科专家、实习医师、医学生
- **图像标注功能**：支持多种诊断选项和置信度评级
- **数据集管理**：创建、组织和管理医学图像数据集
- **进度跟踪**：实时统计标注进度和用户表现
- **本地测试**：无需数据库，使用Mock数据快速测试

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- npm

### 一键启动（推荐）
```bash
cd /home/droot/medc-img-annotation-app
./start_system.sh
```

### 手动启动

#### 1. 启动后端
```bash
cd backend
./start_local.sh
```

#### 2. 启动前端（新终端）
```bash
cd frontend  
./start_frontend.sh
```

### 3. 访问系统
- 前端地址: http://localhost:3000
- 后端API: http://localhost:5000/api
- 测试账户:
  - 管理员: admin/admin123
  - 医师: doctor/doctor123
  - 学生: student/student123

## 🏗️ 技术架构

### 后端 (Backend)
- **框架**: Python Flask 3.0+
- **认证**: JWT (JSON Web Token)
- **API文档**: Flask-RESTX (Swagger)
- **文件存储**: 本地存储
- **数据存储**: 内存Mock数据（无需数据库）

### 前端 (Frontend)
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI组件**: Ant Design 5.0+
- **路由**: React Router v6
- **HTTP客户端**: Axios

## 📁 项目结构

```
medc-img-annotation-app/
├── backend/                          # Python Flask 后端
│   ├── app_local.py                 # 主应用文件（本地测试版）
│   ├── config.py                    # 配置文件
│   ├── requirements.txt             # 精简的依赖列表
│   ├── start_local.sh              # 启动脚本
│   ├── .env                        # 环境变量配置
│   └── uploads/                    # 上传文件目录
├── frontend/                        # React 前端
│   ├── src/
│   │   ├── services/               # API服务层
│   │   ├── pages/                  # 页面组件
│   │   └── App.tsx                 # 主应用组件
│   ├── package.json                # 精简的前端依赖
│   └── start_frontend.sh           # 前端启动脚本
├── start_system.sh                 # 一键启动脚本
├── REFACTOR_GUIDE.md              # 重构详细说明
└── README.md                      # 项目说明
```

## � 功能特性

### ✅ 已实现功能
- **用户管理**: 多角色用户系统（放射科专家、实习医师、医学生）
- **认证系统**: JWT认证和角色权限控制
- **数据集管理**: 数据集创建、图像批量上传、统计信息
- **统计面板**: 实时进度跟踪、用户表现统计

### ⏳ 开发中功能
- **图像标注**: 直观的标注界面、诊断选项、置信度评级
- **数据导出**: Excel、CSV、JSON格式导出
- **高级功能**: 数据可视化、质量控制指标

## 🔧 API接口

### 认证相关
- `GET /api/health` - 健康检查
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/profile` - 获取用户信息

### 数据集相关
- `GET /api/datasets` - 获取数据集列表
- `POST /api/datasets` - 创建数据集
- `GET /api/datasets/{id}/images` - 获取数据集图像
- `POST /api/datasets/{id}/upload` - 上传图像

### 标注相关
- `GET /api/diagnosis-options` - 获取诊断选项
- `GET /api/images/{id}/annotation` - 获取图像标注
- `POST /api/images/{id}/annotation` - 保存图像标注
- `GET /api/statistics` - 获取统计信息

## 📝 补充说明

### 主要改进
1. **移除数据库依赖**: 不再需要MongoDB、Redis等外部服务
2. **简化依赖**: 精简了前后端的依赖包，只保留核心功能
3. **本地化测试**: 使用Mock数据，开箱即用
4. **代码重构**: 重新组织了代码结构，提高可维护性
5. **统一启动**: 提供一键启动脚本，简化部署流程

### 配置说明
所有配置都已简化为本地测试模式，无需复杂的环境配置。

## 🧪 测试

启动系统后可以测试以下功能：
1. 用户登录（三种角色）
2. 创建数据集
3. 上传图像文件
4. 查看统计信息
5. 基础的系统导航


**注意**: 本系统仅用于教育和研究目的，不得用于临床诊断。


## 📊 功能特性

### 用户管理
- ✅ 多角色用户系统（放射科专家、实习医师、医学生）
- ✅ 基于角色的权限控制
- ✅ JWT认证和授权
- ✅ 用户资料管理

### 数据集管理
- ✅ 数据集创建和组织
- ✅ 图像批量上传
- ✅ 元数据管理
- ✅ 进度统计和跟踪

### 图像标注
- ✅ 直观的标注界面
- ✅ 多种诊断选项
- ✅ 置信度评级系统
- ✅ 标注历史记录

### 数据导出
- ✅ Excel格式导出
- ✅ CSV格式导出
- ✅ JSON格式导出
- ✅ 统计报告生成

### 统计分析
- ✅ 实时进度跟踪
- ✅ 用户表现统计
- ✅ 数据可视化
- ✅ 质量控制指标

## 🔧 配置说明

### 环境变量配置
```bash
# Flask 应用配置
FLASK_CONFIG=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# MongoDB 配置
MONGODB_URI=mongodb://localhost:27017/medical_annotation
MONGODB_DB=medical_annotation

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret-key

# 文件上传配置
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800

# CORS 配置
CORS_ORIGINS=http://localhost:3000
```

### 数据库配置
```javascript
// MongoDB 索引创建
db.users.createIndex({ "username": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { unique: true })
db.datasets.createIndex({ "name": 1 })
db.images.createIndex({ "dataset_id": 1 })
db.annotations.createIndex({ "image_id": 1, "user_id": 1 }, { unique: true })
```

## 🧪 测试

### 后端测试
```bash
cd backend
python -m pytest tests/
```

### 前端测试
```bash
cd frontend
npm test
```

### 集成测试
```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行测试
npm run test:e2e
```

## 📦 部署

### Docker 部署
```bash
# 构建镜像
docker-compose build

# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d
```

### 传统部署
```bash
# 后端部署
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# 前端部署
cd frontend
npm run build
# 将 dist 目录部署到 Web 服务器
```

## 🛡️ 安全考虑

- JWT令牌过期和刷新机制
- 密码哈希和盐值处理
- 文件上传类型和大小限制
- SQL注入和XSS防护
- HTTPS强制和安全头设置

## 📈 性能优化

- 数据库查询优化和索引
- 图像压缩和缓存
- 前端代码分割和懒加载
- CDN静态资源分发
- Redis缓存策略

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📝 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基础用户管理功能
- 图像标注核心功能
- 数据导出功能

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系我们

- 项目维护者: [yufa]
- 邮箱: yfaugustin@foxmail.com
- 项目主页: https://github.com/your-username/medc-img-annotation-app


---

**注意**: 本系统仅用于教育和研究目的，不得用于临床诊断。
