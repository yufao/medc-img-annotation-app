
# 前端说明

React + Vite 实现的医学图像标注系统前端。

## 快速开始

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

## 主要功能

- 数据集管理
- 图像标注
- 用户管理
- 进度统计
- 数据导出

## 开发说明

- 路由与应用外壳在 `src/router/Root.jsx`
- 标注与图片选择等业务组件位于 `src/components/**`
- Vite 配置代理到后端 5000 端口
- 使用 React Hooks 管理状态

更多详情请参考主项目 README.md
		4) 仍无则显示“已完成”
- 提交后：重复上述逻辑，避免误判

2025-08-16：修复“仍有未标注却提示完成”的问题，具体实现见 `components/annotation/Annotate.jsx` 中 `fetchImage` 与 `handleSubmit`。

## 故障排查

- 无法加载图片：检查浏览器控制台与网络面板；确认 `/static/img/...` 是否可访问
- 标注后未跳转：查看控制台日志（前端已添加详细日志），确认后端 `/next_image`、`/images_with_annotations` 响应

## 主要文件

- `index.html`：主模板
- `src/main.jsx`：入口挂载（渲染 `router/Root.jsx`）
- `src/router/Root.jsx`：路由与页面布局
- `src/components/annotation/Annotate.jsx`：标注主面板（取图/提交/跳转）
- `src/components/annotation/ImageSelector.jsx`：选择/修改标注

## 变更记录（前端增量）

- 2025-12-05：UI 调整
	- 将“选择图片/修改标注”按钮从标注页底部迁移到顶部工具区，并弱化为小号幽灵样式，减少干扰
	- 在“选择数据集”页面与“标注主界面”页眉右侧新增“登出”按钮，清理会话后返回登录页
	- 样式新增：`top-actions`、`page-tools` 容器与 `btn-xs`/`btn-sm`/`btn-ghost`/`btn-outline` 辅助类
	- “选择图片”页面不再显示“登出/返回”按钮，保持列表操作专注
	- “选择数据集”页面的“登出”按钮置于白色卡片右上角，增强一致性与可达性

## 升级说明：从 App.jsx 迁移到 Root.jsx

自 2025-10 起，前端从“单文件 `App.jsx` 内联多页面”切换为“基于 `react-router` 的路由外壳 `src/router/Root.jsx` + 业务组件分层”的结构：

- 入口不再是 `src/App.jsx`，而是 `src/main.jsx` 渲染的 `src/router/Root.jsx`
- 页面/业务逻辑拆分到 `src/components/**`，例如标注主面板在 `components/annotation/Annotate.jsx`
- 旧文件 `src/App.jsx` 已移除；文档描述全部指向新结构

你的代码适配：
- 如需修改标注行为（取图、提交流程、上一张回退等），编辑 `components/annotation/Annotate.jsx`
- 如需调整“选择图片/修改标注”的排序或分页，编辑 `components/annotation/ImageSelector.jsx`
- 如需改导航或页眉 Logo，编辑 `router/Root.jsx`

回滚/对比：
- 如必须参考旧实现，可从仓库历史提交中查看已删除的 `src/App.jsx` 版本（git 历史）
