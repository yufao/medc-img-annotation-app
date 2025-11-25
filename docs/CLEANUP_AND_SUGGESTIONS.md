# 清理与优化建议（未执行，待你确认）

## 一、拟清理项（空文件/无用文件/重复文件）
- backend/app/routes.py（暂保留用于兼容；生产建议禁用，待两周观察后再物理删除）
- 根目录零散测试文件：test_improvements.py、backend/test_*.py（迁移至 tests/ 后删除原位置）
- 未使用的部署脚本/占位文件（已清理 package-online/offline.sh）
- 重复样式文件（auth.css/admin.css 出现重复项，后续可合并）

备注：批量删除前会先新建分支并跑一轮冒烟。

## 二、测试收敛
- 统一 tests/ 目录；增加 pytest.ini：
  - testpaths = tests backend/tests
  - addopts = -q
- 引入最小集成测试（/api/healthz、/api/datasets、/api/annotate 流程）。

## 三、项目结构建议
- 后端
  - repositories 层补全（现 dataset_repository 存在，其他可按需补齐），服务层保持轻薄。
  - 为 annotations 建组合索引（dataset_id, expert_id, image_id）。
  - 将 user_config 切换至数据库管理（密码哈希、角色、权限）。
- 前端
  - 引入 UI 组件库（AntD）统一按钮/表单/提示风格；
  - 将 Annotate 内部逻辑拆分（数据获取、副作用、交互）便于测试与维护；
  - 避免全量 images_with_annotations 调用，更多使用分页与 next_image。
- DevOps
  - 增加 gunicorn+nginx 部署模板与 systemd；
  - 添加 CI：lint + test + 打包。

## 四、性能优化建议
- 统计接口添加短时缓存（现有服务层已做 15s 缓存，可扩展至全局缓存中间件）。
- 图片预加载与“提前取下一张”。
- Mongo 查询增加投影与必要索引。


