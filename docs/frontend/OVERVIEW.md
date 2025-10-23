# 前端模块说明与使用

基于 React + Vite 实现，按「页面/组件/状态/API 客户端」划分，覆盖登录、数据集管理、图片标注与导出。

## 目录结构

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js          # 基础请求封装（后端 5000 端口代理）
│   ├── components/
│   │   ├── admin/
│   │   │   └── DatasetManager.jsx   # 数据集/标签/图片管理
│   │   ├── annotation/
│   │   │   ├── Annotate.jsx         # 标注主面板（取图/提交/跳转）
│   │   │   ├── ImageSelector.jsx     # 按数据集选择图片
│   │   │   └── ExportButton.jsx      # 导出 Excel
│   │   ├── common/
│   │   │   └── ProgressPanel.jsx     # 统计与进度
│   │   ├── DatasetSelect.jsx
│   │   └── Login.jsx
│   ├── hooks/
│   ├── router/
│   ├── store/
│   ├── styles/
│   ├── router/
│   │   └── Root.jsx            # 应用外壳与页面路由
│   └── main.jsx
├── public/
├── vite.config.js
└── nginx.conf
```

## 关键交互流程（标注）

1. 登录 -> 选择数据集
2. 获取图片：
   - 优先 `/api/images_with_annotations`，筛出第一张「未标注」
   - 如无未标注，调用 `/api/datasets/{id}/statistics` 校验
   - 如统计显示未完成仍无未标注，回退 `/api/next_image`
3. 提交标注：`POST /api/annotate`，随后重复步骤 2 取下一张

注：该策略已在 2025-08-16 修复中落实，避免「明明有未标注却提示完成」。

## 本地开发

```bash
cd frontend
npm install
npm run dev
```
默认代理到 `http://localhost:5000`，可在 `vite.config.js` 中调整。

## 与后端的接口约定

- 详见 `docs/backend/API_REFERENCE.md`
- 统一将 `username` 作为 `expert_id` 传递
- 所有管理员操作须带 `role=admin`

## 多选标注（规划）

- 数据集 `multi_select` 为 true 时，前端允许在标注面板中选择多个标签并批量提交
- 初期以 UI 状态支持为主，后端接口将在 Phase 5 扩展

## 升级说明：从 App.jsx 到 Root.jsx

- 旧版将页面与逻辑集中在单文件 `src/App.jsx`，现已迁移到基于路由的外壳 `src/router/Root.jsx`
- 标注核心逻辑位于 `components/annotation/Annotate.jsx`，图片选择位于 `components/annotation/ImageSelector.jsx`
- 入口由 `src/main.jsx` 统一渲染 `Root`
- 若按照旧文档查找 `App.jsx`，请改查上述位置；如需参考旧实现，请查看 Git 历史中的 `src/App.jsx`
