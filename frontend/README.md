
# 医学图像标注系统前端

本项目为医学图像标注系统的前端部分，基于 React + Vite 构建。

## 项目结构

- `src/`：前端源代码目录，包含主入口和核心组件。
- `index.html`：主页面模板，挂载 React 应用。
- `vite.config.js`：Vite 配置文件，包含开发代理等设置。

## 启动开发环境

```bash
cd frontend
npm install
npm run dev
```

浏览器访问 [http://localhost:3000](http://localhost:3000)

## 代理说明

前端通过 `vite.config.js` 配置了 `/api` 和 `/static` 的代理，开发时会自动转发到后端服务（默认端口 5000）。

## 主要文件注释说明

- `index.html`：页面基础设置，挂载点及入口说明。
- `src/main.jsx`：React 应用入口，负责挂载主组件。
- `src/App.jsx`：包含详细注释，说明各组件和核心逻辑。

如需进一步开发或部署，请参考后端 README 及相关文档。
