## 标准化生产更新流程（无 Docker）

本指南适用于非 Docker 部署：后端 Flask 通过 Gunicorn + systemd 持久运行，Nginx 负责前端静态与后端反代，MongoDB 提供数据。前端使用 Vite 构建的静态产物（dist）。

目录默认：
- 项目根：`/opt/medc-img-annotation-app`
- 后端：`/opt/medc-img-annotation-app/backend`
- 前端：`/opt/medc-img-annotation-app/frontend`
- 图片目录：`/data/medc/static/img`（按需调整）
- systemd 服务名：`medc-annot`（示例）
- Nginx 站点：`/etc/nginx/conf.d/medc-annot.conf`

> 若你的实际路径不同，请在执行前替换为你的路径与服务名。

---

## 0) 快速前置检查（30 秒）

```bash
python --version
node -v
npm -v
systemctl status medc-annot --no-pager || true
nginx -t
```

---

## 1) Git 更新代码

```bash
cd /opt/medc-img-annotation-app
git fetch --all
git checkout main
git pull --ff-only
git log --oneline -n 5
git diff --name-only HEAD~1..HEAD
```

如生产机不应有本地改动，可先清理或暂存：

```bash
git status
git stash push -m "prod-local"  # 仅当有未提交改动时
```

---

## 2) 后端依赖与配置

```bash
cd /opt/medc-img-annotation-app/backend
/opt/conda/envs/medc/bin/pip install -r requirements.txt
```

确认 systemd 环境变量（推荐放在 service 或 EnvironmentFile）：
- `DISABLE_LEGACY_ROUTES=1`（禁用旧路由，避免覆盖新蓝图）
- `MONGO_URI`、`MONGO_DB`（或兼容变量）
- `SECRET_KEY`、`JWT_SECRET_KEY`（生产值）
- `PYTHONUNBUFFERED=1`

修改后需重载守护进程：

```bash
sudo systemctl daemon-reload
```

---

## 3) 前端构建与发布（Vite）

在生产机构建：

```bash
cd /opt/medc-img-annotation-app/frontend
npm ci
npm run build
```

或使用版本化发布（软链接便于回滚）：

```bash
release_dir=/opt/releases/medc-annot/$(date +%Y%m%d_%H%M%S)
mkdir -p "$release_dir"
cp -r /opt/medc-img-annotation-app/frontend/dist "$release_dir"/
ln -sfn "$release_dir/dist" /opt/medc-img-annotation-app/frontend/dist
```

> 如在本地构建完成，再上传 `dist/` 到生产相同目录亦可。

---

## 4) Nginx 配置要点（一次配置，后续沿用）

关键点：
- `index.html` 禁缓存，避免加载旧入口；
- `/assets/`（哈希产物）使用长期缓存（immutable）；
- `/static/img/` alias 到你的图片目录；
- `/api/` 反代到 Gunicorn（端口需一致，例如 127.0.0.1:8000）。

示例（片段）：

```nginx
server {
  listen 80;
  server_name your.domain.com;

  root /opt/medc-img-annotation-app/frontend/dist;

  location = /index.html {
    add_header Cache-Control "no-store, no-cache, must-revalidate";
  }
  location / { try_files $uri /index.html; }

  location /assets/ {
    add_header Cache-Control "public, max-age=31536000, immutable";
    try_files $uri =404;
  }

  location /static/img/ {
    alias /data/medc/static/img/;  # 按实际路径调整
    add_header Cache-Control "public, max-age=604800";
  }

  location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;  # 确认与 Gunicorn 一致
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 64m;
    proxy_read_timeout 120s;
  }
}
```

检测与重载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 5) 后端平滑重启

```bash
sudo systemctl restart medc-annot
sudo systemctl status medc-annot --no-pager
curl -sS http://127.0.0.1:8000/api/healthz
```

> 若 Gunicorn 监听 5000，请将上面的 8000 改为 5000，并同步更新 Nginx。

---

## 6) 回归验证（关键路径）

- 浏览器强制刷新（Ctrl+F5）；
- 打开 Network 面板：
  - 点击“上一张”，看到 `POST /api/prev_image`（请求体包含 `by:'last_annotated'` 与 `current_image_id`）；
  - 提交标注，看到 `/api/annotate` 与 `/api/next_image`；
  - 若测试多标签数据集：确认 `POST /api/annotate` 载荷包含 `label_ids` 数组；
- 图片显示与标题 ID 同步变化（前端 `<img>` 已带 `?v=image_id`）。

---

## 7) 快速回滚（1 分钟）

- 前端（软链接回滚）：

```bash
ls -lt /opt/releases/medc-annot
ln -sfn /opt/releases/medc-annot/<上一版>/dist /opt/medc-img-annotation-app/frontend/dist
sudo systemctl reload nginx
```

- 后端（回退到上一个稳定提交或 tag）：

```bash
cd /opt/medc-img-annotation-app
git checkout <previous-tag-or-commit>
cd backend && /opt/conda/envs/medc/bin/pip install -r requirements.txt
sudo systemctl restart medc-annot
```

---

## 8) 避免更新失败的要点

- 路由优先级：生产务必 `DISABLE_LEGACY_ROUTES=1`，避免旧路由覆盖新实现；
- 端口一致性：Gunicorn 监听端口与 Nginx 反代/健康检查一致；
- 前端缓存策略：`index.html` no-store，`/assets/` immutable；
- 图片路径：Nginx `alias` 指向正确目录，权限足够；
- 依赖一致性：`pip install -r requirements.txt`、`npm ci`；
- 可观测：systemd 输出日志位置固定，便于第一时间定位；
- 回滚友好：前端软链接版本化，后端保留上一个 tag。

---

## 9) 附：systemd 服务示例

```ini
[Unit]
Description=MedC Annotation Backend (Gunicorn)
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/opt/medc-img-annotation-app/backend
Environment=DISABLE_LEGACY_ROUTES=1
Environment=MONGO_URI=mongodb://127.0.0.1:27017/
Environment=MONGO_DB=medical_annotation
Environment=SECRET_KEY=your-prod-secret
Environment=JWT_SECRET_KEY=your-jwt-secret
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/conda/envs/medc/bin/gunicorn -w 4 -b 127.0.0.1:8000 'app:create_app()'
Restart=always
RestartSec=2
StandardOutput=append:/var/log/medc/gunicorn.out.log
StandardError=append:/var/log/medc/gunicorn.err.log

[Install]
WantedBy=multi-user.target
```

---

## 10) 附：Nginx 站点示例

```nginx
server {
  listen 80;
  server_name your.domain.com;

  root /opt/medc-img-annotation-app/frontend/dist;

  location = /index.html {
    add_header Cache-Control "no-store, no-cache, must-revalidate";
  }
  location / { try_files $uri /index.html; }

  location /assets/ {
    add_header Cache-Control "public, max-age=31536000, immutable";
    try_files $uri =404;
  }

  location /static/img/ {
    alias /data/medc/static/img/;
    add_header Cache-Control "public, max-age=604800";
  }

  location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 64m;
    proxy_read_timeout 120s;
  }
}
```

---

## 11) 最简检查清单（每次更新照此走）

- [ ] `git pull --ff-only` 成功无本地冲突；
- [ ] `pip install -r requirements.txt` 完成；
- [ ] `npm ci && npm run build` 完成（或 dist 已上传）；
- [ ] systemd 含 `DISABLE_LEGACY_ROUTES=1`，端口与 Nginx 对齐；
- [ ] `nginx -t` 通过并已 reload；
- [ ] `curl 127.0.0.1:<port>/api/healthz` 通过；
- [ ] 浏览器强刷，Network 面板看到 `POST /api/prev_image`；
- [ ] 前端“上一张/提交并下一张”回归通过。
