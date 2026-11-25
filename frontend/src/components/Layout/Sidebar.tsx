/**
 * 侧边栏组件
 * 主导航菜单，支持折叠、当前页高亮
 * 菜单项从后端 /api/plugins 动态获取（新增插件自动出现），
 * 加载失败时回退到本地默认菜单，保证可用性。
 */

import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { getPlugins, type MenuItem } from '@/api/system';
import { getMenuIcon } from './menuIcons';

// 默认菜单（后端不可用时的兜底）
const defaultMenuItems: MenuItem[] = [
  { key: 'home', label: '工作台', icon: 'home', path: '/home', order: 0 },
  { key: 'knowledge-base', label: '知识库', icon: 'book', path: '/knowledge-bases', order: 10 },
  { key: 'tech-experts', label: '技术专家组', icon: 'brain', path: '/tech-experts', order: 20 },
  { key: 'wechat-writer', label: '公众号写作', icon: 'edit', path: '/wechat-writer', order: 20 },
  { key: 'user-profile', label: '个人中心', icon: 'user', path: '/profile', order: 100 },
];

// 即将上线的功能（灰显，保持本地）
const upcomingItems = [
  { key: 'projects', label: '项目管理', icon: 'calendar' },
  { key: 'data-analysis', label: '数据分析', icon: 'chart' },
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
  const [menuItems, setMenuItems] = useState<MenuItem[]>(defaultMenuItems);

  // 从后端加载动态菜单
  useEffect(() => {
    let cancelled = false;
    getPlugins()
      .then((data) => {
        if (cancelled || !data?.menus?.length) return;
        setMenuItems(data.menus);
      })
      .catch(() => {
        // 后端不可达时保留默认菜单，不影响使用
      });
    return () => {
      cancelled = true;
    };
  }, []);

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
        {/* 主菜单（后端动态） */}
        <div className="px-3 space-y-1">
          {menuItems.map((item) => (
            <Link
              key={item.key}
              to={item.path || '/home'}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                item.path && isActive(item.path)
                  ? 'bg-primary-50 text-primary-600 font-medium'
                  : 'text-text-secondary hover:bg-gray-50 hover:text-text'
              }`}
              title={!expanded ? item.label : undefined}
            >
              <span className="flex-shrink-0">{getMenuIcon(item.icon)}</span>
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
              <span className="flex-shrink-0 opacity-50">{getMenuIcon(item.icon)}</span>
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
