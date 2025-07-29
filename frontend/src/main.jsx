
// 前端入口文件，挂载 React 应用到页面 root 节点
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// 渲染主应用组件
createRoot(document.getElementById('root')).render(<App />);
