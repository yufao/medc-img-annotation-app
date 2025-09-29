# 20250929 项目总结与说明

本文件为 `PROJECT_SUMMARY.md` 的日期化副本，反映 2025-09-29 的项目状态与变更。

> 最新内容与后续增量请参考未加日期的同名文档。
# 项目总结与说明（2025-09）

本文档汇总了本次清理与优化的项目改动、当前结构说明、关键技术点与后续建议。

## 一、当前项目结构（要点）

- backend/
  - app/
    - api/                 新版蓝图路由（auth、dataset、label、image、annotation、export）
    - services/            业务服务层，承载核心逻辑（dataset/label/image/annotation/export）
    - core/db.py           DB 连接与健康检查
    - user_config.py       内置用户配置（admin/doctor/student）
    - __init__.py          应用工厂，支持禁用旧路由
    - static/              静态资源（图像）
  - run.py                 运行入口
  - db_utils.py            自增序列工具
  - database_init.py       DB 初始化与 schema 升级
- frontend/
  - src/
    - components/          UI 组件（登录、数据集选择、标注、导出等）
    - router/Root.jsx      路由入口
    - styles/              样式（app/annotation/admin/auth）
- docs/
  - PROJECT_OVERVIEW.md    项目总览
  - backend/API_REFERENCE.md API 参考
  - DESIGN_PLAN.md         功能设计与规划
  - TOOLS_AND_SCRIPTS.md   脚本说明
  - CHANGELOG.md           变更记录（新增）

## 二、本次主要改动

1) 数据正确性与一致性
- 标签按数据集过滤（无则回退通用标签），避免导出/合并出现无关标签。
- 管理员导出（expert_id=admin）聚合该数据集所有用户的标注。
- 修复标签创建返回时的 ObjectId 序列化错误。

2) 取图体验优化
- 稳定随机：基于“用户+数据集”生成顺序，保证不同账号顺序不同、同账号稳定。
- 前端提交流程改为 next_image 优先，减少等待并遵循稳定随机序。

3) 旧路由下线
- 增加 DISABLE_LEGACY_ROUTES=1 开关并完成物理删除 routes.py。

4) 交互与样式
- 提交按钮三态（灰/橙/蓝）与提交后即时恢复。

## 三、测试与验证建议

- 基本流程：登录 -> 选数据集 -> 标注数张 -> 导出 -> 校验标注覆盖范围与标签表。
- 多账号对比：dtr002、dtr003 在同一数据集的取图顺序应不同。
- 边界：无标签/无图片/无标注的导出与页面提示。

## 四、后续优化建议（暂不实施）

1) 性能与体验
- 批量预取下一张与图片预加载，减少切换耗时。
- 统计接口加入 ETag/短时缓存，进一步降低请求量。

2) 权限与用户
- 用户从数据库管理（替换 user_config.py），支持密码哈希与角色/项目授权。

3) 数据模型
- 为 annotations 建索引（dataset_id, expert_id, image_id）组合索引，提升查询性能。

4) 部署
- 增加生产环境 gunicorn + nginx 模板与 CI/CD 脚本。

5) 前端
- 引入组件库（如 AntD）以快速规范交互与状态样式；拆分 Annotate 组件内部逻辑。

## 五、兼容性

- 新蓝图路径与返回结构保持与旧接口尽量兼容；如遇行为差异，优先以新版文档为准。

---
以上为本轮调整的汇总说明，详情见 CHANGELOG 与各模块文档。
