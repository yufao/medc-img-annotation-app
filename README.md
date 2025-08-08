# 医学图像标注系统 (Medical Image Annotation System) - 重构版本

一个基于 Web 的医学图像标注系统，支持多角色用户（放射科专家、实习医师、医学生）进行医学图像标## 🌟 功能特性

### ✅ 已实现功能
- **用户管理**: 多角色用户系统（放射科专家、实习医师、医学生）
- **认证系统**### 补充说明

### 主要改进
1. **移除数据库依赖**: 不再需要数据库等外部服务
2. **简化依赖**: 精简了前后端的依赖包，只保留核心功能
3. **本地化测试**: 使用Mock数据，开箱即用
4. **代码重构**: 重新组织了代码结构，提高可维护性
5. **统一启动**: 提供一键启动脚本，简化部署流程
6. **界面美化**: 双LOGO设计、渐变背景、现代化UI
7. **智能编号**: 数据集自动编号，支持目录扩展
8. **导出优化**: 分数据集导出，便于数据管理

### 配置说明
所有配置都已简化为本地测试模式，无需复杂的环境配置。

### LOGO设置
1. 将实验室LOGO保存为 `frontend/public/实验室LOGO.png`
2. 将学校LOGO保存为 `frontend/public/JNU-LOGO.jpg`
3. 系统会自动在顶部显示双LOGO（64x64像素，美化样式）

### 数据集管理
1. 在 `backend/app/static/` 下创建数据集文件夹（文件夹名即数据集代码）
2. 将图片放入对应文件夹
3. 系统启动时自动扫描并分配编号
4. 支持运行时动态添加新数据集限控制
- **数据集管理**: 数据集创建、图像批量上传、统计信息
- **统计面板**: 实时进度跟踪、用户表现统计
- **界面美化**: 双LOGO顶部栏、渐变背景、进度环形图
- **图片查看**: 缩放、拖拽、选中高亮功能
- **智能编号**: 按数据集自动编号（如D01-0001格式）

### ⏳ 开发中功能
- **图像标注**: 直观的标注界面、诊断选项、置信度评级
- **数据导出**: 分数据集Excel导出、全量多Sheet导出
- **高级功能**: 数据可视化、质量控制指标

## �️ 数据集扩展设计

### 目录结构式数据集管理
系统采用目录扫描方式自动发现数据集，后续扩展新数据集只需：

1. **新增数据集**: 在 `/backend/app/static/` 下创建新文件夹（如 `DLung/`）
2. **放入图片**: 将图片文件放入该文件夹
3. **自动识别**: 系统启动时自动扫描并创建数据集记录

### 智能编号系统
- **全局ID**: `image_id` 系统内唯一，用于数据库关联
- **数据集序号**: `seq_in_dataset` 每个数据集从1开始递增
- **展示编号**: `display_id` 格式为 `<数据集代码>-<零填充序号>`
  - 示例: `D01-0001`, `DRetina-0023`, `DLung-0156`

### 导出策略
- **单数据集导出**: `GET /api/export?dataset_id=xxx` → 单个Excel工作表
- **全量导出**: `GET /api/export_all` → 多工作表文件（每数据集一个Sheet）
- **字段包含**: 数据集信息、全局ID、展示编号、标注详情、专家信息

### 可扩展优势
- ✅ **零代码扩展**: 只需文件系统操作，无需修改代码
- ✅ **编号稳定**: 历史编号不受新增数据集影响
- ✅ **分工明确**: 不同数据集可分配给不同专家团队
- ✅ **导出灵活**: 支持按需导出单个或全部数据集📋 重要说明: 本版本已完成重构，移除了本地测试时的数据库依赖，可使用Mock数据进行本地测试。**

## 🎯 项目概述

本系统旨在为医学教育和研究提供一个专业的图像标注平台，支持：

- **多角色用户管理**：放射科专家、实习医师、医学生
- **图像标注功能**：支持多种诊断选项和置信度评级
- **数据集管理**：创建、组织和管理医学图像数据集
- **智能图片编号**：按数据集自动编号，支持可扩展架构
- **进度跟踪**：实时统计标注进度和用户表现
- **本地测试**：无需数据库，使用Mock数据快速测试
- **分数据集导出**：支持单数据集或全量导出Excel

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
- **图片管理**: 目录扫描式数据集发现
- **编号系统**: 全局ID + 数据集内序号双轨制

### 前端 (Frontend)
- **框架**: React 18 + JSX
- **构建工具**: Vite
- **UI样式**: 自定义CSS + 渐变设计
- **HTTP客户端**: Axios
- **界面特色**: 双LOGO展示、进度环形图、图片缩放拖拽

## 📁 项目结构

```
medc-img-annotation-app/
├── backend/                          # Python Flask 后端
│   ├── app_local.py                 # 主应用文件（本地测试版）
│   ├── config.py                    # 配置文件
│   ├── requirements.txt             # 精简的依赖列表
│   ├── start_local.sh              # 启动脚本
│   ├── .env                        # 环境变量配置
│   ├── uploads/                    # 上传文件目录
│   └── app/
│       └── static/                 # 静态图片目录
│           ├── D01/               # 数据集D01 (目录名即数据集编码)
│           ├── DRetina/          # 数据集DRetina
│           └── ...               # 更多数据集...
├── frontend/                        # React 前端
│   ├── public/                     # 公共静态资源
│   │   ├── 实验室LOGO.png         # 实验室标志
│   │   └── JNU-LOGO.jpg          # 学校标志
│   ├── src/
│   │   ├── services/               # API服务层
│   │   ├── pages/                  # 页面组件
│   │   └── App.jsx                # 主应用组件（美化版）
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
6. 双LOGO顶部栏显示
7. 图片缩放拖拽功能
8. 进度环形图显示
9. 智能编号系统
10. 分数据集导出功能

### 界面测试要点
- **顶部栏**: 确认双LOGO正确显示（64x64像素）
- **图片查看**: 测试缩放（滚轮）、拖拽（鼠标）、选中高亮
- **进度统计**: 查看环形进度图和数字统计
- **编号显示**: 确认图片显示格式为 `D01-0001` 样式
- **导出功能**: 测试单数据集和全量导出

### 扩展测试
1. 在 `backend/app/static/` 下创建新文件夹（如 `DTest/`）
2. 放入几张测试图片
3. 重启系统，确认新数据集自动出现
4. 测试新数据集的编号是否正确（如 `DTest-0001`）


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
系统已移除传统数据库依赖，改用以下方式：

```javascript
// 数据集自动发现（目录扫描）
backend/app/static/
├── D01/          # 数据集D01，包含CT图像
├── DRetina/      # 数据集DRetina，包含眼底图像
├── DLung/        # 数据集DLung，包含肺部X光
└── ...           # 其他数据集

// 内存数据结构
datasets = {
  "D01": { id: 1, name: "胸部CT数据集", active: true },
  "DRetina": { id: 2, name: "眼底图像数据集", active: true }
}

images = {
  1: { id: 1, dataset_id: 1, filename: "ct_001.jpg", seq_in_dataset: 1, display_id: "D01-0001" },
  2: { id: 2, dataset_id: 1, filename: "ct_002.jpg", seq_in_dataset: 2, display_id: "D01-0002" }
}
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

### v2.0.0 (2025-01-08)
- **界面美化**: 双LOGO顶部栏设计，64x64像素优化显示
- **智能编号**: 实现数据集内自动编号（D01-0001格式）
- **扩展架构**: 支持目录扫描式数据集管理，零代码扩展
- **图片查看**: 新增缩放、拖拽、选中高亮功能
- **进度可视化**: 环形进度图和统计卡片
- **导出分离**: 分数据集导出和全量多Sheet导出
- **代码重构**: 移除数据库依赖，使用内存Mock数据

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
