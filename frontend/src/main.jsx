
// 前端入口文件，挂载 React 应用到页面 root 节点
import React from 'react';
import { createRoot } from 'react-dom/client';
// 保留旧 App 作为回退；新版本使用基于 react-router 的 Root
import Root from './router/Root';
import './styles/app.css';

// 渲染主应用组件
createRoot(document.getElementById('root')).render(<Root />);

