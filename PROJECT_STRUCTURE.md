# 项目文件说明

## 📁 核心文件结构

```
medc-img-annotation-app/
├── 🚀 管理脚本
│   ├── manage.sh                   # 统一管理脚本（推荐使用）
│   ├── docker-deploy.sh            # Docker 构建部署脚本
│   ├── create-online-package.sh    # 创建在线部署包
│   └── create-offline-package.sh   # 创建离线部署包
│
├── 🐳 Docker 配置
│   ├── docker-compose.yml          # 开发环境配置
│   └── docker-compose.prod.yml     # 生产环境配置
│
├── 🔧 后端 (Flask)
│   ├── app/                        # 应用核心代码
│   ├── requirements.txt            # Python 依赖
│   ├── run.py                      # 启动文件
│   ├── Dockerfile                  # Docker 构建文件
│   └── README.md                   # 后端说明
│
├── 🎨 前端 (React)
│   ├── src/                        # React 源码
│   ├── package.json                # Node.js 依赖
│   ├── vite.config.js             # Vite 配置
│   ├── Dockerfile                  # Docker 构建文件
│   ├── deploy_static.sh            # 静态部署脚本
│   └── README.md                   # 前端说明
│
└── 📄 文档
    ├── README.md                   # 主项目说明
    └── .gitignore                  # Git 忽略文件
```

## 🔧 主要脚本功能

### manage.sh（推荐使用）
- 一键管理整个项目
- 支持开发/生产环境切换
- 包含构建、部署、监控等功能

### docker-deploy.sh
- 专用于 Docker 环境的构建和部署
- 包含镜像推送功能

### create-*-package.sh
- 创建可分发的部署包
- 支持在线/离线两种模式

## 🚀 推荐使用流程

1. **开发阶段**：
   ```bash
   ./manage.sh dev
   ```

2. **生产部署**：
   ```bash
   ./manage.sh build
   ./manage.sh start
   ```

3. **创建部署包**：
   ```bash
   ./manage.sh package
   ```

4. **日常管理**：
   ```bash
   ./manage.sh status    # 查看状态
   ./manage.sh logs      # 查看日志
   ./manage.sh restart   # 重启服务
   ```
