# 数据安全和Git操作说明

## Git操作对数据库的影响分析

### ✅ **不会受影响的数据**

#### 1. MongoDB数据库数据
- **数据集信息**：所有通过系统创建的数据集定义
- **图片元数据**：上传的图片信息记录
- **标注数据**：所有用户的标注记录
- **标签定义**：各数据集的标签配置

**原因：** MongoDB数据存储在Docker卷或本地数据目录中，不属于Git版本控制范围。

#### 2. 上传的图片文件
- **位置：** `backend/app/static/img/` 目录
- **状态：** 该目录在 `.gitignore` 中被排除
- **安全性：** Git操作不会影响已上传的图片

#### 3. 系统日志
- **位置：** `logs/` 目录  
- **状态：** 日志文件通常也被Git忽略

### ⚠️ **可能受影响的配置**

#### 1. 用户配置文件
- **文件：** `backend/app/user_config.py`
- **影响：** 如果远程版本有更新，可能会覆盖本地用户配置
- **解决方案：** 见下方保护策略

#### 2. 环境配置
- **文件：** `backend/.env`
- **影响：** 本地环境配置可能被重置
- **解决方案：** 备份后重新配置

## 数据保护策略

### 1. 用户配置保护

```bash
# 在Git拉取前备份用户配置
cp backend/app/user_config.py backend/app/user_config.py.backup

# Git操作
git pull

# 如果配置被覆盖，恢复备份
cp backend/app/user_config.py.backup backend/app/user_config.py
```

### 2. 环境配置保护

```bash
# 备份环境配置
cp backend/.env backend/.env.backup

# Git操作后恢复
cp backend/.env.backup backend/.env
```

### 3. 完整的安全更新流程

```bash
# 1. 备份关键配置
mkdir -p backup/$(date +%Y%m%d_%H%M%S)
cp backend/app/user_config.py backup/$(date +%Y%m%d_%H%M%S)/
cp backend/.env backup/$(date +%Y%m%d_%H%M%S)/

# 2. 停止服务（可选，防止数据不一致）
./manage.sh stop

# 3. 拉取更新
git pull

# 4. 检查配置文件是否需要恢复
# 比较备份文件和当前文件的差异
diff backup/$(date +%Y%m%d_%H%M%S)/user_config.py backend/app/user_config.py

# 5. 如需要，恢复配置
cp backup/$(date +%Y%m%d_%H%M%S)/user_config.py backend/app/user_config.py

# 6. 重启服务
./manage.sh start
```

## Docker数据持久化

### 数据卷配置
项目使用Docker卷来持久化数据：

```yaml
# docker-compose.yml 中的卷配置
volumes:
  mongodb_data:
    driver: local
```

### 数据存储位置
- **MongoDB数据：** Docker卷 `mongodb_data`
- **上传图片：** `backend/app/static/img/`（映射到容器内）
- **日志文件：** `logs/` 目录

## 建议的工作流程

### 日常开发
```bash
# 安全的代码更新流程
git stash push -m "保存本地配置更改"
git pull
git stash pop
```

### 生产环境更新
```bash
# 1. 创建完整备份
./manage.sh backup  # 如果有备份脚本

# 2. 停止服务
./manage.sh stop

# 3. 备份配置
mkdir backup_configs
cp backend/app/user_config.py backup_configs/
cp backend/.env backup_configs/

# 4. 更新代码
git pull

# 5. 恢复必要配置
cp backup_configs/user_config.py backend/app/user_config.py
cp backup_configs/.env backend/.env

# 6. 重启服务
./manage.sh start
```

## 验证数据完整性

### 检查数据库
```bash
# 连接到MongoDB容器检查数据
docker exec -it $(docker ps -qf "name=mongodb") mongo

# 在mongo shell中
use medical_annotation
db.datasets.count()      // 检查数据集数量
db.annotations.count()   // 检查标注数量
db.images.count()        // 检查图片记录数量
```

### 检查图片文件
```bash
# 统计上传的图片数量
find backend/app/static/img -type f -name "*.jpg" -o -name "*.png" -o -name "*.jpeg" | wc -l
```

## 总结

✅ **数据库数据和上传图片是安全的** - Git操作不会影响这些数据

⚠️ **注意保护用户配置文件** - 建议在Git操作前备份用户配置

🔒 **推荐使用完整的备份流程** - 确保在任何更新操作前都有完整备份

📝 **定期备份** - 建议定期备份重要配置和数据库