/**
 * 侧边栏组件
 * 主导航菜单，支持折叠、当前页高亮
 */

import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

// 菜单项配置
const menuItems = [
  {
    key: 'home',
    label: '工作台',
    path: '/home',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    key: 'knowledge',
    label: '知识库',
    path: '/knowledge',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
  {
    key: 'tech-experts',
    label: '技术专家组',
    path: '/tech-experts',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
];

// 即将上线的功能（灰显）
const upcomingItems = [
  {
    key: 'projects',
    label: '项目管理',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
  },
  {
    key: 'data-analysis',
    label: '数据分析',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
];

interface SidebarProps {
  /** 是否折叠 */
  collapsed?: boolean;
  /** 折叠状态变化回调 */
  onCollapse?: (collapsed: boolean) => void;
}

export default function Sidebar({ collapsed = false, onCollapse }: SidebarProps) {
  const location = useLocation();
  const [expanded, setExpanded] = useState(!collapsed);

  const handleToggle = () => {
    const newExpanded = !expanded;
    setExpanded(newExpanded);
    onCollapse?.(!newExpanded);
  };

  // 判断当前路径是否匹配
  const isActive = (path: string) => {
    return location.pathname.startsWith(path);
  };

  return (
    <aside
      className={`h-full bg-white border-r border-gray-100 flex flex-col transition-all duration-300 ${
        expanded ? 'w-60' : 'w-16'
      }`}
    >
      {/* Logo 区域 */}
      <div className="h-16 flex items-center px-4 border-b border-gray-50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-primary-500 flex items-center justify-center text-white font-bold text-lg flex-shrink-0">
            青
          </div>
          {expanded && (
            <span className="font-semibold text-text text-lg whitespace-nowrap">
              青萍小台
            </span>
          )}
        </div>
      </div>

      {/* 菜单区域 */}
      <nav className="flex-1 py-4 overflow-y-auto">
        {/* 主菜单 */}
        <div className="px-3 space-y-1">
          {menuItems.map((item) => (
            <Link
              key={item.key}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                isActive(item.path)
                  ? 'bg-primary-50 text-primary-600 font-medium'
                  : 'text-text-secondary hover:bg-gray-50 hover:text-text'
              }`}
              title={!expanded ? item.label : undefined}
            >
              <span className="flex-shrink-0">{item.icon}</span>
              {expanded && <span className="whitespace-nowrap">{item.label}</span>}
            </Link>
          ))}
        </div>

        {/* 分隔线 */}
        {expanded && (
          <div className="mx-4 my-4 border-t border-gray-100" />
        )}

        {/* 即将上线 */}
        {expanded && (
          <div className="px-4 mb-2">
            <span className="text-xs text-text-tertiary">即将上线</span>
          </div>
        )}

        <div className="px-3 space-y-1">
          {upcomingItems.map((item) => (
            <div
              key={item.key}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 cursor-not-allowed"
              title={!expanded ? `${item.label}（即将上线）` : undefined}
            >
              <span className="flex-shrink-0 opacity-50">{item.icon}</span>
              {expanded && (
                <span className="whitespace-nowrap opacity-50">
                  {item.label}
                  <span className="ml-2 text-xs">(即将上线)</span>
                </span>
              )}
            </div>
          ))}
        </div>
      </nav>

      {/* 底部折叠按钮 */}
      <div className="p-3 border-t border-gray-50">
        <button
          onClick={handleToggle}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-text-secondary hover:bg-gray-50 transition-colors"
          title={expanded ? '收起菜单' : '展开菜单'}
        >
          <svg
            className={`w-5 h-5 transition-transform ${expanded ? '' : 'rotate-180'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
          {expanded && <span className="text-sm">收起</span>}
        </button>
      </div>
    </aside>
  );
}
