/**
 * 注册页面
 * 支持用户名/密码注册
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useUserStore } from '@/store/useUserStore';
import Button from '@/components/Common/Button';
import Input from '@/components/Common/Input';

export default function Register() {
  const navigate = useNavigate();
  const { register, loading } = useUserStore();

  // 表单状态
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [formErrors, setFormErrors] = useState<{ username?: string; password?: string; confirmPassword?: string }>({});
  const [registerError, setRegisterError] = useState('');

  // 表单验证
  const validate = (): boolean => {
    const errors: { username?: string; password?: string; confirmPassword?: string } = {};

    if (!username.trim()) {
      errors.username = '请输入用户名';
    } else if (username.trim().length < 3) {
      errors.username = '用户名至少3个字符';
    }

    if (!password) {
      errors.password = '请输入密码';
    } else if (password.length < 6) {
      errors.password = '密码长度不能少于6位';
    }

    if (!confirmPassword) {
      errors.confirmPassword = '请确认密码';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = '两次输入的密码不一致';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // 提交注册
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegisterError('');

    if (!validate()) return;

    try {
      await register({ username: username.trim(), password });
      // 注册成功，跳转到登录页
      navigate('/login', { replace: true, state: { message: '注册成功，请登录' } });
    } catch (err) {
      const message = err instanceof Error ? err.message : '注册失败';
      setRegisterError(message);
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

        {/* 注册表单 */}
        <div className="bg-white rounded-2xl shadow-large p-8">
          <h2 className="text-xl font-semibold text-text mb-6">注册账号</h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 用户名 */}
            <Input
              label="用户名"
              type="text"
              placeholder="请输入用户名（至少3个字符）"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              error={!!formErrors.username}
              errorMessage={formErrors.username}
              required
              autoComplete="username"
            />

            {/* 密码 */}
            <Input
              label="密码"
              type="password"
              placeholder="请输入密码（至少6位）"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={!!formErrors.password}
              errorMessage={formErrors.password}
              required
              autoComplete="new-password"
            />

            {/* 确认密码 */}
            <Input
              label="确认密码"
              type="password"
              placeholder="请再次输入密码"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              error={!!formErrors.confirmPassword}
              errorMessage={formErrors.confirmPassword}
              required
              autoComplete="new-password"
            />

            {/* 错误提示 */}
            {registerError && (
              <div className="p-3 bg-danger-50 border border-danger-100 rounded-lg text-danger-600 text-sm flex items-center gap-2">
                <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {registerError}
              </div>
            )}

            {/* 注册按钮 */}
            <Button
              type="submit"
              block
              size="lg"
              loading={loading.sessions /* 使用通用 loading */}
            >
              注 册
            </Button>
          </form>

          {/* 底部提示 */}
          <div className="mt-6 text-center text-sm text-text-tertiary">
            已有账号？
            <Link to="/login" className="text-primary-600 hover:text-primary-700 ml-1">
              立即登录
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
