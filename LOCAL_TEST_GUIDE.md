# 🏥 医学图像标注系统 - 本地测试指南

## 📋 目录结构
```
medc-img-annotation-app/
├── backend/                    # Python Flask 后端
│   ├── app/                   # 应用代码
│   ├── requirements.txt       # Python依赖
│   ├── .env                   # 环境配置
│   ├── run_test.sh           # 完整测试脚本
│   ├── test_mongodb.py       # MongoDB连接测试
│   └── MONGODB_SETUP.md      # MongoDB配置详细说明
├── frontend/                  # React前端
│   ├── src/                  # 前端源码
│   ├── package.json          # Node.js依赖
│   └── start_frontend.sh     # 前端启动脚本
└── docker-compose.yml        # Docker配置（可选）
```

## 🚀 快速启动

### 方法1: 使用Windows MongoDB（推荐）

1. **配置Windows MongoDB**
   ```bash
   # 在Windows系统中启动MongoDB
   net start MongoDB
   
   # 获取Windows IP地址
   ipconfig
   ```

2. **配置Linux后端**
   ```bash
   cd /home/droot/medc-img-annotation-app/backend
   
   # 编辑.env文件，设置您的Windows IP
   nano .env
   # 修改: MONGODB_URI=mongodb://[您的Windows IP]:27017/medical_annotation
   
   # 运行完整测试
   ./run_test.sh
   ```

3. **启动前端**
   ```bash
   # 新开一个终端
   cd /home/droot/medc-img-annotation-app/frontend
   ./start_frontend.sh
   ```

### 方法2: 使用Mock数据模式

如果无法连接MongoDB，系统会自动使用Mock数据模式：

```bash
# 启动后端（自动回退到Mock模式）
cd /home/droot/medc-img-annotation-app/backend
./run_test.sh

# 启动前端
cd /home/droot/medc-img-annotation-app/frontend
./start_frontend.sh
```

## 🔧 详细配置步骤

### 1. MongoDB连接配置

#### Windows端配置：
1. 确保MongoDB服务正在运行
2. 配置MongoDB允许外部连接（编辑mongod.cfg）
3. 配置防火墙允许端口27017

#### Linux端配置：
1. 编辑`.env`文件设置正确的MongoDB URI
2. 运行连接测试：`python3 test_mongodb.py`

详细配置说明请参考：`backend/MONGODB_SETUP.md`

### 2. 环境变量配置

编辑`backend/.env`文件：
```bash
# MongoDB配置
MONGODB_URI=mongodb://192.168.1.100:27017/medical_annotation
MONGODB_DB=medical_annotation

# Flask配置
FLASK_CONFIG=development
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

### 3. 依赖安装

#### 后端依赖：
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 前端依赖：
```bash
cd frontend
npm install
```

## 🌐 访问地址

- **后端API**: http://localhost:5000
- **API文档**: http://localhost:5000/doc
- **前端应用**: http://localhost:3000

## 🔑 测试账户

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 全部功能 |
| 医生 | doctor | doctor123 | 标注、查看 |
| 学生 | student | student123 | 标注 |

## 📊 功能测试

1. **用户认证**
   - 登录/注销
   - 角色权限验证

2. **数据集管理**
   - 查看数据集列表
   - 数据集详情
   - 标注进度统计

3. **图像标注**
   - 获取下一张图像
   - 选择诊断结果
   - 设置置信度
   - 添加备注

4. **数据导出**
   - 导出标注数据
   - 多种格式支持（CSV、JSON）

## 🔍 故障排除

### MongoDB连接问题
```bash
# 测试MongoDB连接
cd backend
python3 test_mongodb.py

# 查看详细错误信息
python3 test_mongodb.py --help
```

### 端口冲突
如果端口被占用，修改以下配置：
- 后端：修改`.env`中的`FLASK_PORT`
- 前端：修改`vite.config.ts`中的端口设置

### 防火墙问题
确保以下端口开放：
- 3000 (前端)
- 5000 (后端)
- 27017 (MongoDB)

## 📝 开发模式

### 后端开发
```bash
cd backend
source venv/bin/activate
export FLASK_DEBUG=True
python run.py
```

### 前端开发
```bash
cd frontend
npm run dev
```

## 📚 API文档

启动后端服务后，访问：http://localhost:5000/doc

包含所有API端点的详细说明和测试界面。

## 🐳 Docker部署（可选）

如果安装了Docker，可以使用Docker Compose：
```bash
cd /home/droot/medc-img-annotation-app
docker-compose up -d
```

## 📞 技术支持

遇到问题时，请检查：
1. 系统日志
2. 浏览器控制台
3. 网络连接状态
4. MongoDB服务状态

---

💡 **提示**: 如果MongoDB连接失败，系统会自动使用Mock数据模式，仍然可以测试所有功能
