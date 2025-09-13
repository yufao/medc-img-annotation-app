
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

- 核心代码在 `src/App.jsx`
- Vite 配置代理到后端 5000 端口
- 使用 React Hooks 管理状态

更多详情请参考主项目 README.md
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
