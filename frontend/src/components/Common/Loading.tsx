/**
 * 加载组件
 * 支持全屏加载和局部加载
 */

interface LoadingProps {
  /** 加载文字 */
  text?: string;
  /** 是否全屏 */
  fullscreen?: boolean;
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg';
}

const sizeMap = {
  sm: 'w-5 h-5 border-2',
  md: 'w-8 h-8 border-2',
  lg: 'w-12 h-12 border-3',
};

export default function Loading({ text = '加载中...', fullscreen = false, size = 'md' }: LoadingProps) {
  const spinner = (
    <div className="flex flex-col items-center justify-center gap-3">
      <div
        className={`${sizeMap[size]} border-primary-200 border-t-primary-500 rounded-full animate-spin`}
      />
      {text && <span className="text-sm text-text-secondary">{text}</span>}
    </div>
  );

  if (fullscreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 backdrop-blur-sm">
        {spinner}
      </div>
    );
  }

  return spinner;
}

/**
 * 页面加载骨架屏
 */
export function PageSkeleton() {
  return (
    <div className="animate-pulse">
      {/* 标题骨架 */}
      <div className="h-8 w-48 bg-gray-200 rounded mb-6" />

      {/* 卡片骨架 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl p-5 shadow-soft">
            <div className="h-4 w-20 bg-gray-200 rounded mb-3" />
            <div className="h-8 w-24 bg-gray-100 rounded" />
          </div>
        ))}
      </div>

      {/* 内容区骨架 */}
      <div className="bg-white rounded-xl p-6 shadow-soft">
        <div className="h-5 w-32 bg-gray-200 rounded mb-4" />
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-4 bg-gray-100 rounded" style={{ width: `${80 - i * 10}%` }} />
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * 按钮加载中状态（小圆点）
 */
export function Spinner({ className = '' }: { className?: string }) {
  return (
    <div
      className={`${className} w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin`}
    />
  );
}
