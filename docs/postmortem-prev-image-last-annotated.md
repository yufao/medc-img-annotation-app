## 复盘：前端“上一张”未按“最近一次标注”生效的问题（含错误与修复代码）

本复盘记录了“上一张”功能在开发与生产环境中出现的偏差行为、根因分析、关键错误代码与修复、部署层面的踩坑与对策，以及最终的规范做法与验证清单。可用于后续培训与回溯。

### 摘要

- 现象：点击“上一张”后，标题中的图片 ID 改变，但画面不变；浏览器网络面板无 `/api/prev_image` 请求，仅有 `/api/images_with_annotations`；生产健康检查端口不一致导致误判后端异常。
- 根因：
  1) 前端“上一张”仍走本地 history/列表兜底，未调用后端权威接口；
  2) 旧路由（legacy）与新蓝图并存，可能覆盖新语义；
  3) 浏览器缓存/相同 filename 造成的视觉不变；
  4) 生产健康检查使用了与进程不一致的端口号。
- 解决：
  - 前端改为调用 `/api/prev_image`，传 `by:'last_annotated'` 与 `current_image_id`；图片使用 key 与 `?v=image_id` 缓存破除；
  - 后端服务层实现“最近一次标注”语义，并在生产禁用 legacy 路由；
  - Nginx 对 index.html 禁缓存，/assets/ 长缓存；
  - 端口统一（Gunicorn 与 Nginx、健康检查一致）。

---

## 一、问题表现

- 前端：
  - 点击“上一张”，标题中的 `image_id` 改变，但显示的图片不变；
  - Network 面板只有 `/api/images_with_annotations`，看不到 `/api/prev_image`。
- 后端：
  - 对应点击时段没有 `/api/prev_image` 的访问记录；
  - 生产健康检查 `curl 127.0.0.1:8000/api/healthz` 连接被拒绝（进程监听 5000）。

## 二、深层原因

1) 前端行为未更新到“服务端驱动”的上一张：仍用本地 history/列表推断上一张，无法反映“最近一次标注”的真实语义。

2) 旧路由覆盖新逻辑：legacy routes 也注册了 `/api/prev_image`（按顺序上一张），若未禁用 legacy，可能覆盖新蓝图。

3) 缓存与数据特性：相同 filename 或浏览器缓存导致画面看似不变，即便 `image_id` 已变；若多个 `image_id` 指向同一文件名，这一现象更加明显（非功能 bug）。

4) 端口不一致：Gunicorn 进程监听与健康检查/反代使用的端口不同，造成误判“服务未起”。

---

## 三、关键错误与修复对比（含代码片段）

### 1) 前端 `Annotate.jsx`：错误的“上一张”实现（未调用后端）

错误（示例）——只操作本地历史或调用列表接口“猜测上一张”，未按“最近一次标注”语义：

```javascript
// 错误示例：未调用 /api/prev_image，而是依赖本地 history/列表兜底（语义不一致）
const handlePrev = async () => {
  const h = historyRef.current;
  if (h.idx > 0) {
    h.idx -= 1;
    const prevId = h.stack[h.idx];
    // 继续用列表接口查询 meta ...
    const { data } = await api.post('/images_with_annotations', { include_all: true /* ... */ });
    const found = data.find(it => String(it.image_id) === String(prevId));
    if (found) { setCurrentImage(found); return; }
    setCurrentImage({ image_id: prevId, filename: img?.filename });
  }
};
```

正确修复——调用后端权威接口并强制图片刷新：

文件：`frontend/src/components/annotation/Annotate.jsx`

```javascript
// 使用服务端“最近一次标注”的语义获取上一张
const handlePrev = async () => {
  if (!dataset || !user) return;
  setIsLoading(true); setError(null);
  try {
    const body = { dataset_id: dataset.id, expert_id: user, role, by: 'last_annotated' };
    if (img?.image_id) body.current_image_id = img.image_id;
    const resp = await api.post('/prev_image', body);
    const data = resp.data || {};
    if (data.image_id) {
      const meta = { image_id: data.image_id, filename: data.filename };
      setCurrentImage(meta, { push: true });
      prefetchNextStableRandom(meta.image_id);
    } else {
      setError('没有上一张可回退');
    }
  } catch (e) { setError('获取上一张失败，请重试'); }
  finally { setIsLoading(false); }
};

// 图片渲染：通过 key 与版本参数强制刷新
<img
  key={`${img.image_id}-${img.filename || ''}`}
  src={`/static/img/${img.filename}?v=${img.image_id}`}
  alt={`图片ID: ${img.image_id}`}
  loading="lazy"
  draggable={false}
/> 
```

### 2) 后端 `annotation_api.py`：`/api/prev_image` 入参不足

错误——未接收 `expert_id`、`by`、`current_image_id`，无法实现“最近一次标注”：

```python
@bp.route('/api/prev_image', methods=['POST'])
def prev_image():
    data = request.json or {}
    ds_id = data.get('dataset_id')
    curr_image_id = data.get('image_id')
    result = annotation_service.prev_image(ds_id, curr_image_id)
    return jsonify(result)
```

正确修复——补齐参数并传递到服务层：

文件：`backend/app/api/annotation_api.py`

```python
@bp.route('/api/prev_image', methods=['POST'])
def prev_image():
    data = request.json or {}
    ds_id = data.get('dataset_id')
    curr_image_id = data.get('image_id') or data.get('current_image_id')
    expert_id = data.get('expert_id')
    by = data.get('by', 'last_annotated')
    result = annotation_service.prev_image(ds_id, curr_image_id, expert_id=expert_id, by=by)
    return jsonify(result)
```

### 3) 后端服务层 `annotation_service.py`：实现“最近一次标注”

关键实现（节选）——当 `by='last_annotated'` 且传入 `expert_id` 时，按 `record_id`/`datetime` 倒序选取上一张；若与当前相同则取更早一条：

文件：`backend/app/services/annotation_service.py`

```python
def prev_image(self, dataset_id: int, current_image_id: Optional[int] = None, *, expert_id: Optional[str] = None, by: str = 'sequential') -> Dict[str, Any]:
    self.ensure_db()
    ds_id = self._normalize_dataset_id(dataset_id)

    if by == 'last_annotated' and expert_id:
        cursor = self.db.annotations.find(
            {'dataset_id': ds_id, 'expert_id': expert_id},
            {'_id': 0, 'image_id': 1, 'record_id': 1, 'datetime': 1}
        ).sort([('record_id', -1), ('datetime', -1)])
        anns = list(cursor)
        if not anns:
            return {"msg": "no previous image"}

        pick = anns[0]
        if current_image_id is not None and pick.get('image_id') == current_image_id:
            if len(anns) > 1:
                pick = anns[1]
            else:
                return {"msg": "no previous image"}

        image_doc = self.db.images.find_one({'image_id': pick.get('image_id')}, {'_id': 0, 'image_id': 1, 'image_path': 1})
        if image_doc:
            return {
                'image_id': image_doc.get('image_id'),
                'filename': self._filename_from_path(image_doc.get('image_path', ''))
            }
        return { 'image_id': pick.get('image_id'), 'filename': '' }

    # 兜底：按 image_id 升序的前一个（旧行为）
    # ...
```

### 4) 路由并存冲突：禁用 legacy 路由

错误现象——legacy routes 也注册 `/api/prev_image`，按注册顺序可能覆盖新蓝图的实现。

正确做法——在生产/开发默认禁用 legacy：

文件：`backend/app/__init__.py`

```python
from os import getenv
disable_legacy = getenv('DISABLE_LEGACY_ROUTES', '0') in ('1', 'true', 'True')
if not disable_legacy:
    from app.routes import register_routes
    register_routes(app)
register_all(app)  # 新蓝图
```

systemd（关键环境变量）：

```ini
Environment=DISABLE_LEGACY_ROUTES=1
```

### 5) 生产端口不一致：健康检查失败

错误——Gunicorn 监听 0.0.0.0:5000，但健康检查用 127.0.0.1:8000。

修复二选一：

方案A（推荐）统一改为 8000：

```ini
ExecStart=/path/to/gunicorn -w 4 -b 127.0.0.1:8000 'app:create_app()'
```

Nginx：

```nginx
location /api/ { proxy_pass http://127.0.0.1:8000/api/; }
```

方案B 保持 5000，则健康检查与 Nginx 都改用 5000。

### 6) Nginx 缓存策略（避免旧入口页）

正确策略——index.html 禁缓存；/assets/（哈希产物）长缓存；图片静态 alias：

```nginx
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
```

---

## 四、解决方案汇总

1) 前端将“上一张”改为调用后端 `/api/prev_image`，传 `by:'last_annotated'` 和 `current_image_id`；
2) 图片元素使用 key 与 `?v=image_id` 确保强制重渲染；
3) 后端服务层实现“最近一次标注”，API 支持 expert_id/by/current_image_id；
4) 生产/开发中禁用 legacy 路由，避免接口覆盖；
5) Nginx 对 index.html 禁缓存，/assets/ 长缓存，图片正确 alias；
6) 统一 Gunicorn/Nginx/健康检查的端口。

## 五、走过的弯路

- 试图在前端用本地 history/列表推断上一张，导致语义与后端真实状态不一致；
- 一度将问题归因于浏览器缓存/同名文件，但根因是旧逻辑/旧 bundle 与路由覆盖；
- 健康检查端口与进程监听端口不一致，误判后端宕机。

## 六、验证与回归清单

- 浏览器 Network：点击“上一张”出现 `POST /api/prev_image`（body 含 `by:'last_annotated'`、`current_image_id`）；
- 图片与标题 ID 同步变化；
- 后端日志出现 `/api/prev_image`；
- `curl 127.0.0.1:<port>/api/healthz` 通过；
- Nginx `nginx -t` 通过，index.html 确认 no-store；
- legacy 路由禁用（检查 `DISABLE_LEGACY_ROUTES=1`）。

---

## 七、文件与路径参考

- 前端：`frontend/src/components/annotation/Annotate.jsx`
- 后端 API：`backend/app/api/annotation_api.py`
- 后端服务：`backend/app/services/annotation_service.py`
- Flask 工厂/路由注册：`backend/app/__init__.py`
- 生产 systemd：`/etc/systemd/system/<service>.service`
- Nginx 站点：`/etc/nginx/conf.d/<site>.conf`

如需将本复盘内容同步为团队知识库，可直接引用本文档。
