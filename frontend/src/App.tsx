/**
 * 应用入口组件
 * 配置路由、全局布局、鉴权等
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Sidebar from '@/components/Layout/Sidebar';
import TopBar from '@/components/Layout/TopBar';
import Login from '@/pages/Login';
import Home from '@/pages/Home';
import KnowledgeBase from '@/pages/KnowledgeBase';
import TechExperts from '@/pages/TechExperts';
import { useUserStore } from '@/store/useUserStore';
import Loading from '@/components/Common/Loading';

// 页面标题映射
const pageTitles: Record<string, string> = {
  '/home': '工作台',
  '/knowledge': '知识库',
  '/tech-experts': '技术专家组',
};

/**
 * 受保护的路由组件
 * 需要登录才能访问
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, user } = useUserStore();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // 简单的鉴权检查
    const checkAuth = () => {
      if (!token) {
        // 没有 token，跳转到登录页
        setIsChecking(false);
        return;
      }
      setIsChecking(false);
    };

    checkAuth();
  }, [token, user]);

  if (isChecking) {
    return <Loading fullscreen text="加载中..." />;
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

/**
 * 主布局组件
 * 包含侧边栏和顶部栏
 */
function MainLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [pageTitle, setPageTitle] = useState('');

  useEffect(() => {
    // 根据当前路径设置页面标题
    const path = window.location.pathname;
    const title = pageTitles[path] || '';
    setPageTitle(title);
  }, []);

  return (
    <div className="h-screen flex bg-bg overflow-hidden">
      {/* 侧边栏 */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onCollapse={setSidebarCollapsed}
      />

      {/* 主内容区 */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* 顶部栏 */}
        <TopBar title={pageTitle} />

        {/* 页面内容 */}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/home" element={<Home />} />
            <Route path="/knowledge" element={<KnowledgeBase />} />
            <Route path="/tech-experts" element={<TechExperts />} />
            <Route path="*" element={<Navigate to="/home" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

/**
 * 根组件
 */
function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 登录页（不需要布局） */}
        <Route path="/login" element={<Login />} />

        {/* 需要鉴权的页面 */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
