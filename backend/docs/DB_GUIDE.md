## 数据库配置与迁移指南

本项目当前后端已统一 Mongo 配置，解决早期混用 `local` / `medical_annotation` 及 `172.*` IP 的混乱。

### 1. 变量优先级

```
MONGO_URI (首选) -> MONGODB_URI (兼容) -> 默认 mongodb://localhost:27017/
MONGO_DB  (首选) -> MONGODB_DB  (兼容) -> 默认 medical_annotation
```

推荐：只在 `.env` 中使用 `MONGO_URI` 与 `MONGO_DB`。

### 2. 初次部署

1. 复制 `backend/.env.example` 为 `backend/.env`
2. 修改 `MONGO_URI` 指向：
   - 单机同服务器：`mongodb://localhost:27017/`
   - 远程独立 Mongo：`mongodb://user:pass@host:27017/`
   - Mongo Atlas：官方连接字符串（注意 URL 编码账号密码）
3. 根据环境改 `MONGO_DB`（建议：`medc_annotation_dev` / `medc_annotation_prod`）
4. （可选）运行初始化脚本：`python setup_database.py` 或从前端/管理端导入数据

### 3. 从旧库 local 迁移

如果之前在 `.env` 里是：

```
MONGODB_URI=mongodb://192.168.xxx.xxx:27017/local
MONGODB_DB=local
```

现在想迁移到：

```
MONGO_URI=mongodb://192.168.xxx.xxx:27017/
MONGO_DB=medical_annotation
```

执行：

```bash
cd backend
python migrate_db.py --src-db local --dst-db medical_annotation
```

Dry Run：

```bash
python migrate_db.py --src-db local --dst-db medical_annotation --dry-run
```

### 4. 管理调试端点

`GET /api/admin/db_status?role=admin`

返回：
```
{
  connected: true,
  mongo_uri: "mongodb://localhost:27017/",
  db_name: "medical_annotation",
  collections: { datasets: 2, images: 20, ... }
}
```

### 5. Git Pull 不覆盖本地配置

`.env` 已在 `.gitignore` 中，不会被覆盖。仓库提供 `.env.example` 作为基线。新服务器：

```bash
cp backend/.env.example backend/.env
vim backend/.env  # 修改生产参数
```

### 6. 多环境策略 (可选自动命名)

如果希望按环境自动命名，可在 `.env` 里只保留 `MONGO_URI`，并在启动前导出：

```bash
export APP_ENV=production
export MONGO_DB=medc_annotation_${APP_ENV}
```

或在部署脚本中生成：

```bash
if [ -z "${MONGO_DB}" ]; then
  export MONGO_DB="medc_annotation_${APP_ENV:-dev}"
fi
```

### 7. 远程开发 (WSL <-> Windows)

最初使用 `192.168.*` 直连 Windows Mongo，可改成：

1. 在 Windows 上为 Mongo 绑定 0.0.0.0 监听（注意安全）
2. 或使用 SSH 隧道：
   ```bash
   ssh -N -L 27018:localhost:27017 user@windows-host
   export MONGO_URI=mongodb://localhost:27018/
   ```
3. 或使用 Docker / Compose 统一本地开发环境

### 8. 脚本差异说明

| 脚本 | 作用 | 是否写数据 |
|------|------|------------|
| `setup_database.py` | 快速重置并写入示例数据 | 是（清空后重建） |
| `db_utils.py` | 序列维护/清理重复 | 看子命令 |
| `migrate_db.py` | 旧库 -> 新库复制 | 是（受 --dry-run / --force 控制） |

### 9. 安全与索引

确保生产：
1. 使用账号密码 + 最低权限用户 (只访问目标库)
2. 建立复合索引（标注查询已创建）
3. 定期备份：`mongodump --db <MONGO_DB> --out backup/$(date +%F)`

### 10. 常见问题

| 问题 | 可能原因 | 解决 |
|------|----------|------|
| API 报 500 数据库连接不可用 | Mongo 未启动或 URI 不可达 | 检查 `db_status` 端点、网络、防火墙 |
| 数据集“消失” | 指向了不同 DB (local vs medical_annotation) | 使用 `migrate_db.py` 迁移或切换回原 DB |
| 标注 ID 冲突 | 旧数据无序列或重复 | 运行 `python db_utils.py cleanup` |

---
如需进一步自动化（CI 中初始化数据、按分支区分 DB 等），可继续扩展部署脚本。
