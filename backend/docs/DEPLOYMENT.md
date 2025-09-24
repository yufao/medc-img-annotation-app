# 部署与运行模式指南

## 1. 运行模式对比

| 模式 | 启动命令 | 特征 | 适用场景 |
|------|----------|------|----------|
| Dev (Flask 内置) | `python run.py` | 自动重载 / 单进程 | 本地开发调试 |
| Gunicorn (生产建议) | `gunicorn -c deploy/gunicorn.conf.py 'app:create_app()'` | 多 worker / 更稳定 | 生产 / 预发 |
| Systemd 服务 | `systemctl start medc-backend` | 自恢复 / 日志接入 journald | 长期运行 |
| Docker (可扩展) | (未来可加 compose) | 隔离 / 易扩缩 | 云原生部署 |

## 2. 前置准备
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 修改生产配置
```

## 3. 数据库迁移 / 初始化
```bash
# 旧 local -> 新库（Dry Run）：
python migrate_db.py --src-db local --dst-db medc_annotation_prod --dry-run

# 实际迁移：
python migrate_db.py --src-db local --dst-db medc_annotation_prod

# 查看数据库状态：
curl 'http://localhost:5000/api/admin/db_status?role=admin'
```

## 4. 健康检查
`GET /api/healthz` 返回：`{ ok: true, db_connected: true/false }`

## 5. Systemd 部署
1. 复制 service：
```bash
sudo cp deploy/medc-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable medc-backend
sudo systemctl start medc-backend
sudo systemctl status medc-backend
```
2. 日志查看：
```bash
journalctl -u medc-backend -f
```

## 6. 常用运维操作
```bash
# 平滑重启（修改代码后）
systemctl restart medc-backend

# 仅查服务端口连通性
curl -fsS http://127.0.0.1:5000/api/healthz
```

## 7. 配置与环境变量
`.env` 中的数据库与密钥不会被 git 覆盖；有示例 `.env.example` 作为基线。

核心：
```
MONGO_URI=mongodb://your-host:27017/
MONGO_DB=medc_annotation_prod
SECRET_KEY=***
JWT_SECRET_KEY=***
```

## 8. 故障快速排查
| 现象 | 排查点 |
|------|--------|
| /api/datasets 500 | 看 `/api/admin/db_status` 是否 connected=false |
| healthz db_connected=false | 检查 Mongo 进程 / 网络 / 认证 |
| 迁移脚本连接拒绝 | 是否 load_dotenv、URI 正确、端口可达 |
| 数据“丢失” | 可能在旧库 `local`，执行迁移脚本复制 |

## 9. 下一步可扩展
- Nginx 前置反向代理 + 静态资源缓存
- Docker 镜像与 Compose 一键化
- Prometheus 指标（请求耗时、Mongo 健康）
- CI/CD：push 触发自动部署
