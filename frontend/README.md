
# 医学图像标注系统前端

React + Vite 实现的前端应用，连接后端 Flask API 完成数据集管理与标注。

## 结构

- `src/`：源代码，核心在 `App.jsx`
- `vite.config.js`：开发代理（转发 `/api` 与 `/static` 到后端 5000）
- `start_frontend.sh`：开发模式启动脚本

## 开发启动

```bash
cd frontend
npm install
npm run dev   # 或 ./start_frontend.sh
```

访问 http://localhost:3000

## 取图与提交流程（与后端配合）

- 入口组件：`src/App.jsx` 中的 `Annotate`
- 获取图片：
	- 有 image_id 时，先从 `/images_with_annotations` 精确取该图与标注
	- 无 image_id 时：
		1) `/images_with_annotations` 全量 -> 选第一张未标注
		2) 无未标注则 `/datasets/{id}/statistics` 核验是否完成
		3) 如统计仍显示未完成，回退 `/next_image`
		4) 仍无则显示“已完成”
- 提交后：重复上述逻辑，避免误判

2025-08-16：修复“仍有未标注却提示完成”的问题，具体实现见 `App.jsx` 中 `fetchImage` 与 `handleSubmit`。

## 故障排查

- 无法加载图片：检查浏览器控制台与网络面板；确认 `/static/img/...` 是否可访问
- 标注后未跳转：查看控制台日志（前端已添加详细日志），确认后端 `/next_image`、`/images_with_annotations` 响应

## 主要文件

- `index.html`：主模板
- `src/main.jsx`：入口挂载
- `src/App.jsx`：页面、数据流与标注逻辑（已补充详细注释）
