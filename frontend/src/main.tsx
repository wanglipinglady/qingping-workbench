/**
 * 应用入口文件
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// 获取根元素
const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('未找到根元素 #root');
}

// 创建 React 根节点并渲染应用
ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
