/**
 * 通用模态框组件
 * 支持标题、底部操作区、关闭按钮
 */

import { ReactNode, useEffect } from 'react';

interface ModalProps {
  /** 是否显示 */
  visible: boolean;
  /** 标题 */
  title?: string;
  /** 内容 */
  children: ReactNode;
  /** 底部操作区 */
  footer?: ReactNode;
  /** 关闭回调 */
  onClose: () => void;
  /** 是否点击遮罩关闭 */
  maskClosable?: boolean;
  /** 宽度 */
  width?: string | number;
  /** 是否显示关闭按钮 */
  closable?: boolean;
}

export default function Modal({
  visible,
  title,
  children,
  footer,
  onClose,
  maskClosable = true,
  width = 480,
  closable = true,
}: ModalProps) {
  // 阻止背景滚动
  useEffect(() => {
    if (visible) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [visible]);

  // ESC 键关闭
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && visible) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [visible, onClose]);

  if (!visible) return null;

  const handleMaskClick = () => {
    if (maskClosable) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 遮罩层 */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fade-in"
        onClick={handleMaskClick}
      />

      {/* 模态框内容 */}
      <div
        className="relative bg-white rounded-2xl shadow-large animate-slide-up"
        style={{ width: typeof width === 'number' ? `${width}px` : width }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        {(title || closable) && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <h3 className="text-lg font-semibold text-text">{title}</h3>
            {closable && (
              <button
                onClick={onClose}
                className="p-1 -mr-1 rounded-lg text-text-tertiary hover:text-text-secondary hover:bg-gray-100 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        )}

        {/* 内容区 */}
        <div className="px-6 py-5">{children}</div>

        {/* 底部 */}
        {footer && (
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
