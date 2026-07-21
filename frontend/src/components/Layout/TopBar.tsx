/**
 * 顶部栏组件
 * 包含搜索框、通知、用户菜单
 */

import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUserStore } from '@/store/useUserStore';
import { formatDate } from '@/utils/format';

interface TopBarProps {
  /** 页面标题 */
  title?: string;
}

export default function TopBar({ title }: TopBarProps) {
  const navigate = useNavigate();
  const { user, logout } = useUserStore();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const today = formatDate(new Date(), 'YYYY年MM月DD日 dddd');

  return (
    <header className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-6">
      {/* 左侧：页面标题 */}
      <div className="flex items-center gap-4">
        {title && (
          <h1 className="text-lg font-semibold text-text">{title}</h1>
        )}
        <span className="text-sm text-text-tertiary">{today}</span>
      </div>

      {/* 右侧：操作区 */}
      <div className="flex items-center gap-4">
        {/* 搜索框 */}
        <div className="relative">
          <input
            type="text"
            placeholder="搜索..."
            className="w-64 h-9 pl-10 pr-4 bg-bg-secondary rounded-lg text-sm text-text placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary-200 transition-shadow"
          />
          <svg
            className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        {/* 通知按钮 */}
        <button className="relative p-2 rounded-lg text-text-secondary hover:bg-gray-50 transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          {/* 未读标记 */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-danger-500 rounded-full" />
        </button>

        {/* 用户菜单 */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-3 p-1.5 rounded-lg hover:bg-gray-50 transition-colors"
          >
            {/* 用户头像 */}
            <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center text-white text-sm font-medium">
              {user?.nickname?.charAt(0) || user?.username?.charAt(0) || 'U'}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-sm font-medium text-text">
                {user?.nickname || user?.username || '用户'}
              </div>
              <div className="text-xs text-text-tertiary">
                {user?.role === 'admin' ? '管理员' : '普通用户'}
              </div>
            </div>
            <svg
              className={`w-4 h-4 text-text-tertiary transition-transform ${showUserMenu ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* 下拉菜单 */}
          {showUserMenu && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-large border border-gray-100 py-2 z-50 animate-fade-in">
              <div className="px-4 py-3 border-b border-gray-50">
                <div className="text-sm font-medium text-text">
                  {user?.nickname || user?.username}
                </div>
                <div className="text-xs text-text-tertiary truncate">
                  {user?.email || '未设置邮箱'}
                </div>
              </div>

              <button
                className="w-full px-4 py-2 text-left text-sm text-text-secondary hover:bg-gray-50 flex items-center gap-2"
                onClick={() => {
                  setShowUserMenu(false);
                  // 跳转到个人设置（暂未实现）
                }}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                个人设置
              </button>

              <button
                className="w-full px-4 py-2 text-left text-sm text-text-secondary hover:bg-gray-50 flex items-center gap-2"
                onClick={() => {
                  setShowUserMenu(false);
                  // 跳转到帮助中心（暂未实现）
                }}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                帮助中心
              </button>

              <div className="border-t border-gray-50 my-1" />

              <button
                className="w-full px-4 py-2 text-left text-sm text-danger-500 hover:bg-danger-50 flex items-center gap-2"
                onClick={handleLogout}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                退出登录
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
