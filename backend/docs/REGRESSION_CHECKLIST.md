# 回归快速自测清单 (Phase3 A)

目标：在每次重要后端/服务层改动后，10-15 分钟内人工或脚本快速验证核心功能未回归。

## 验证环境准备
- 启动后端 Flask 服务（确保已连接 Mongo 或使用内存回退）
- 准备至少 1 个管理员账号、1 个专家账号
- 至少 1 个数据集，包含 >=3 张图片，存在 1~2 条已标注记录

## 通用规则
- 所有成功请求 HTTP 200（创建返回 201），权限不足 403，缺少资源 404
- JSON 响应包含 `msg`、或直接返回数组/对象（列表 API）

## 数据集 /admin
1. GET /api/datasets -> 返回数组且字段包含 id/name/image_count
2. POST /api/admin/datasets {role:admin,name:"ds-regression"} -> 201 且返回 dataset_id
3. POST /api/admin/datasets/<id>/recount {role:admin} -> image_count 与实际图片关联数一致
4. DELETE /api/admin/datasets/<id>?role=admin -> 200 且 deleted_images >=0
5. 非 admin 创建：POST /api/admin/datasets {role:doctor} -> 403

## 图片
6. POST /api/admin/datasets/<id>/images (multipart, role=admin) -> 201 uploaded 数量正确
7. GET /api/datasets/<id>/images?page=1&pageSize=2 -> 返回 <=2 条且包含 annotation 字段

## 标注
8. POST /api/annotate 初次 -> msg=saved
9. POST /api/annotate 同一 image 再次 -> msg=saved (应为更新不报错)
10. POST /api/update_annotation 修改 label -> msg=updated 或 not changed
11. POST /api/next_image -> 返回未标注图片或 msg=done
12. POST /api/images_with_annotations {include_all:false} -> 返回仅未标注项

## 标签
13. GET /api/labels -> 返回全局标签列表
14. POST /api/admin/datasets/<id>/labels 新增 -> 返回插入数量
15. PUT /api/admin/datasets/<id>/labels 覆盖更新 -> 返回更新后数量

## 导出
16. GET /api/export?dataset_id=<id> -> 下载 Excel，含 4+ sheet（标注/图片/标签/数据集信息）

## 用户 / 管理
17. GET /api/admin/users?role=admin -> 返回用户数组
18. GET /api/admin/users?role=doctor -> 403
19. GET /api/admin/users/config?role=admin -> 返回 instructions 数组

## 错误场景
20. GET /api/datasets/999999/statistics -> total_count=0 或合理错误
21. POST /api/admin/datasets (缺少 name) -> 400
22. POST /api/admin/datasets/<id>/images 无文件 -> 400

## 多选 (multi_select) 功能占位 (实现后补充)
- 创建数据集时可传 multi_select=true
- GET /api/datasets 返回该字段（默认 False）
- 标注接口在 multi_select=true 时支持同一 image 写入多 label（后续详细规范）

## 快速脚本思路 (伪示例)
```bash
TOKEN_ADMIN=admin
curl -s http://localhost:5000/api/datasets | jq 'length'
```

## 记录模板
| 序号 | 用例 | 结果 | 备注 |
|------|------|------|------|
| 1 | GET /api/datasets | ✅ | |
| 2 | POST /api/admin/datasets | ✅ | dataset_id=12 |
| .. | ... | | |

---
更新频率：当新增字段 / 新增端点 / 响应结构变化时同步维护。
