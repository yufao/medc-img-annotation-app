# 后端说明

Flask + MongoDB 实现的医学图像标注系统后端服务。

## 快速开始

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

## 主要功能

- 用户认证与角色管理
- 数据集管理
- 图像上传与存储
- 标注数据管理
- 进度统计
- Excel 导出

## API 文档

- `/api/login` - 用户登录
- `/api/datasets` - 数据集管理
- `/api/images` - 图像管理
- `/api/annotations` - 标注管理
- `/api/export` - 数据导出

更多详情请参考主项目 README.md
```

## � 关键端点

- 登录：`POST /api/login`
- 数据集：`GET /api/datasets`，`GET /api/datasets/{id}/statistics`
- 标签：`GET /api/labels`（可带 dataset_id），管理员增改查见 routes
- 图片列表：
	- `POST /api/images_with_annotations`（支持 include_all 分页，返回 annotation 字段）
	- `GET  /api/datasets/{id}/images`（备用列表接口）
- 下一张/上一张：`POST /api/next_image`，`POST /api/prev_image`
- 提交/更新标注：`POST /api/annotate`，`POST /api/update_annotation`
- 导出：`GET /api/export`（dataset_id/expert_id 可选）

说明：`/api/next_image` 会优先返回“当前角色在该数据集中第一张未标注”的图片；`/api/images_with_annotations` 可一次性返回带标注合并信息列表，供前端优先筛选“未标注”。

## 📌 与前端协同（取图与提交流程）

前端在 2025-08-16 更新后：
1) 无指定 image_id 时，先调用 `/api/images_with_annotations` 取全量，再选第一张未标注；如无未标注，再通过 `/api/datasets/{id}/statistics` 确认是否完成，必要时回退 `/api/next_image`；仍无则视为完成。
2) 提交后同样逻辑以避免误判“已完成”。

## 📁 结构

```
backend/
├── app/
│   ├── routes.py         # API 路由
│   ├── static/img/       # 图片目录
│   └── templates/        # （如有）
├── config.py             # 配置（读取 .env）
├── db_utils.py           # 序列与工具
├── run.py                # 启动入口
├── requirements.txt
└── README.md
```

## 🧪 脚本

```bash
# 基础测试
python test_annotation.py
python concurrent_test.py
python test_export.py

# 简单启动
./run_test.sh
```

## 📊 数据结构

- annotations(dataset_id, record_id, image_id, expert_id, label_id, tip, datetime)
- images(image_id, image_path)
- datasets(id, name, description, created_at, image_count, status)
- image_datasets(dataset_id, image_id)
- labels(label_id, label_name, category, dataset_id)
- sequences(_id, sequence_value)

## 🔒 并发与一致性

- 使用 `findOneAndUpdate` 自增序列保证 record_id 唯一
- 标注更新采用 upsert 逻辑（新增/覆盖）避免重复
