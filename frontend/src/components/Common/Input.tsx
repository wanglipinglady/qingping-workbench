/**
 * 通用输入框组件
 * 支持多种类型、尺寸和状态
 */

import { InputHTMLAttributes, forwardRef } from 'react';

type InputSize = 'sm' | 'md' | 'lg';

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** 输入框尺寸 */
  inputSize?: InputSize;
  /** 左侧图标 */
  leftIcon?: React.ReactNode;
  /** 右侧图标 */
  rightIcon?: React.ReactNode;
  /** 错误状态 */
  error?: boolean;
  /** 错误提示文字 */
  errorMessage?: string;
  /** 标签文字 */
  label?: string;
  /** 是否必填 */
  required?: boolean;
}

// 尺寸样式映射
const sizeStyles: Record<InputSize, string> = {
  sm: 'h-8 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-4 text-base',
};

const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  {
    inputSize = 'md',
    leftIcon,
    rightIcon,
    error = false,
    errorMessage,
    label,
    required = false,
    className = '',
    disabled,
    ...rest
  },
  ref
) {
  const baseStyles = `
    w-full rounded-lg border bg-white text-text placeholder-text-tertiary
    transition-all duration-200 focus:outline-none focus:ring-2
    disabled:bg-gray-50 disabled:text-text-tertiary disabled:cursor-not-allowed
  `;

  const stateStyles = error
    ? 'border-danger-300 focus:border-danger-400 focus:ring-danger-100'
    : 'border-gray-200 focus:border-primary-400 focus:ring-primary-100 hover:border-gray-300';

  const iconLeftStyles = leftIcon ? 'pl-10' : '';
  const iconRightStyles = rightIcon ? 'pr-10' : '';

  return (
    <div className="w-full">
      {/* 标签 */}
      {label && (
        <label className="block text-sm font-medium text-text mb-1.5">
          {label}
          {required && <span className="text-danger-500 ml-0.5">*</span>}
        </label>
      )}

      {/* 输入框容器 */}
      <div className="relative">
        {/* 左侧图标 */}
        {leftIcon && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary pointer-events-none">
            {leftIcon}
          </span>
        )}

        {/* 输入框 */}
        <input
          ref={ref}
          className={`${baseStyles} ${stateStyles} ${sizeStyles[inputSize]} ${iconLeftStyles} ${iconRightStyles} ${className}`}
          disabled={disabled}
          {...rest}
        />

        {/* 右侧图标 */}
        {rightIcon && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary pointer-events-none">
            {rightIcon}
          </span>
        )}
      </div>

      {/* 错误提示 */}
      {error && errorMessage && (
        <p className="mt-1 text-xs text-danger-500">{errorMessage}</p>
      )}
    </div>
  );
});

export default Input;
