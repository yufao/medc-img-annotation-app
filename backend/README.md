# 医学图像标注系统后端

基于Flask的医学图像标注系统后端，支持高并发标注操作，使用MongoDB存储数据。

## 🚀 快速开始

### 环境要求
- Python 3.8+
- MongoDB 4.0+
- 推荐使用虚拟环境

### 安装和启动

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 初始化数据库（首次运行）
python setup_database.py

# 启动服务
python run.py
```

### 环境配置

创建 `.env` 文件：
```env
MONGODB_URI=mongodb://172.20.48.1:27017/local
MONGODB_DB=local
```

## 📖 API文档

启动服务后访问：http://localhost:5000/doc

## 🔧 核心特性

- **并发安全的ID生成**：使用MongoDB原子操作生成唯一record_id
- **多角色支持**：支持doctor、student等不同角色的标注
- **数据导出**：支持Excel格式的标注数据导出
- **图像管理**：支持多数据集的图像分类和管理

## 🧪 测试

```bash
# 测试标注功能
python test_annotation.py

# 并发压力测试
python concurrent_test.py

# 测试导出功能
python test_export.py
```

## 📁 项目结构

```
backend/
├── app/                          # Flask应用
│   ├── __init__.py
│   ├── routes.py                 # API路由
│   └── static/                   # 静态文件
├── db_utils.py                   # 数据库工具（自增序列、清理等）
├── setup_database.py             # 数据库初始化
├── test_annotation.py            # 标注功能测试
├── concurrent_test.py            # 并发测试
├── test_export.py               # 导出功能测试
├── requirements.txt              # 依赖包
├── run.py                       # 应用入口
└── README.md                    # 项目文档
```

## 🛠️ 维护和监控

### 检查系统状态
```bash
# 检查序列状态
python db_utils.py status

# 查看数据库内容
python setup_database.py --show
```

### 数据库维护
如果遇到record_id重复问题，运行清理脚本：
```bash
python db_utils.py cleanup
```

检查序列状态：
```bash
python db_utils.py status
```

运行简单并发测试：
```bash
python db_utils.py test
```

## 📊 数据结构

### 核心集合
- **annotations**: 标注数据（dataset_id, record_id, image_id, expert_id, label_id, tip, datetime）
- **images**: 图像信息（image_id, image_path, dataset_id）
- **labels**: 标签定义（label_id, label_name, category）
- **datasets**: 数据集管理（id, name, description）
- **sequences**: 自增序列（_id, sequence_value）

## 🔒 并发安全

系统使用MongoDB的`findOneAndUpdate`原子操作确保record_id的唯一性，完全解决了高并发环境下的重复键问题。所有数据库工具已整合到`db_utils.py`中，提供统一的接口。
