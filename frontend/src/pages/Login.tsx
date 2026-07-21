/**
 * 登录页面
 * 支持用户名/密码登录、记住密码、错误提示
 */

import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useUserStore } from '@/store/useUserStore';
import Button from '@/components/Common/Button';
import Input from '@/components/Common/Input';

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, loading, error, rememberMe, savedUsername, setRememberMe, clearError } = useUserStore();

  // 表单状态
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [formErrors, setFormErrors] = useState<{ username?: string; password?: string }>({});

  // 初始化：如果记住了用户名，自动填充
  useEffect(() => {
    if (rememberMe && savedUsername) {
      setUsername(savedUsername);
    }
  }, [rememberMe, savedUsername]);

  // 清除 API 错误
  useEffect(() => {
    return () => clearError();
  }, [clearError]);

  // 表单验证
  const validate = (): boolean => {
    const errors: { username?: string; password?: string } = {};

    if (!username.trim()) {
      errors.username = '请输入用户名';
    }

    if (!password) {
      errors.password = '请输入密码';
    } else if (password.length < 6) {
      errors.password = '密码长度不能少于6位';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // 提交登录
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    try {
      // 保存记住密码设置
      setRememberMe(rememberMe, username);

      await login({ username: username.trim(), password });

      // 登录成功，跳转到首页或 redirect 地址
      const redirect = searchParams.get('redirect');
      navigate(redirect || '/home', { replace: true });
    } catch (err) {
      // 错误已在 store 中处理
      console.error('登录失败:', err);
    }
  };

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo 和标题 */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-primary-500 flex items-center justify-center text-white text-2xl font-bold shadow-lg">
            青
          </div>
          <h1 className="text-2xl font-bold text-text mb-2">青萍小台</h1>
          <p className="text-text-secondary text-sm">智能知识管理与技术专家协作平台</p>
        </div>

        {/* 登录表单 */}
        <div className="bg-white rounded-2xl shadow-large p-8">
          <h2 className="text-xl font-semibold text-text mb-6">登录账号</h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 用户名 */}
            <Input
              label="用户名"
              type="text"
              placeholder="请输入用户名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              error={!!formErrors.username}
              errorMessage={formErrors.username}
              required
              leftIcon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              }
              autoComplete="username"
            />

            {/* 密码 */}
            <Input
              label="密码"
              type="password"
              placeholder="请输入密码"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={!!formErrors.password}
              errorMessage={formErrors.password}
              required
              leftIcon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              }
              autoComplete="current-password"
            />

            {/* 错误提示 */}
            {error && (
              <div className="p-3 bg-danger-50 border border-danger-100 rounded-lg text-danger-600 text-sm flex items-center gap-2">
                <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {error}
              </div>
            )}

            {/* 记住密码 */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked, username)}
                  className="w-4 h-4 rounded border-gray-300 text-primary-500 focus:ring-primary-500"
                />
                <span className="text-sm text-text-secondary">记住密码</span>
              </label>

              <a href="#" className="text-sm text-primary-600 hover:text-primary-700">
                忘记密码？
              </a>
            </div>

            {/* 登录按钮 */}
            <Button
              type="submit"
              block
              size="lg"
              loading={loading.send || loading.sessions /* 使用通用 loading */}
            >
              登 录
            </Button>
          </form>

          {/* 底部提示 */}
          <div className="mt-6 text-center text-sm text-text-tertiary">
            还没有账号？
            <Link to="/register" className="text-primary-600 hover:text-primary-700 ml-1">
              立即注册
            </Link>
          </div>

          {/* 默认账号提示 */}
          <div className="mt-4 p-3 bg-gray-50 rounded-lg text-xs text-text-tertiary text-center">
            💡 默认管理员账号：<span className="font-mono text-text-secondary">admin</span> / <span className="font-mono text-text-secondary">admin123</span>
          </div>
        </div>

        {/* 底部版权 */}
        <p className="text-center text-xs text-text-tertiary mt-8">
          © 2024 青萍小台. All rights reserved.
        </p>
      </div>
    </div>
  );
}
