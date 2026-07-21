/**
 * 通用按钮组件
 * 支持多种样式变体和尺寸
 */

import { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** 按钮变体 */
  variant?: ButtonVariant;
  /** 按钮尺寸 */
  size?: ButtonSize;
  /** 是否加载中 */
  loading?: boolean;
  /** 是否为块级元素 */
  block?: boolean;
  /** 左侧图标 */
  leftIcon?: ReactNode;
  /** 右侧图标 */
  rightIcon?: ReactNode;
}

// 变体样式映射
const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-primary-500 text-white hover:bg-primary-600 active:bg-primary-700 focus:ring-primary-200',
  secondary:
    'bg-accent-500 text-white hover:bg-accent-600 active:bg-accent-700 focus:ring-accent-200',
  outline:
    'bg-white text-text border border-gray-200 hover:bg-gray-50 hover:border-gray-300 focus:ring-gray-200',
  ghost:
    'bg-transparent text-text-secondary hover:bg-gray-100 focus:ring-gray-200',
  danger:
    'bg-danger-500 text-white hover:bg-danger-600 active:bg-danger-700 focus:ring-danger-200',
};

// 尺寸样式映射
const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm rounded-lg',
  md: 'px-4 py-2 text-sm rounded-lg',
  lg: 'px-6 py-3 text-base rounded-xl',
};

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  block = false,
  leftIcon,
  rightIcon,
  children,
  disabled,
  className = '',
  ...rest
}: ButtonProps) {
  const baseStyles =
    'inline-flex items-center justify-center gap-2 font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed';

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${
        block ? 'w-full' : ''
      } ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && (
        <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {!loading && leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
      {children}
      {!loading && rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
    </button>
  );
}
