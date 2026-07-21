/**
 * Markdown 渲染组件
 * 支持代码高亮、GFM 语法
 */

import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MarkdownRenderProps {
  /** Markdown 内容 */
  content: string;
  /** 是否禁用代码块行号 */
  showLineNumbers?: boolean;
  /** 自定义类名 */
  className?: string;
}

export default function MarkdownRender({
  content,
  showLineNumbers = false,
  className = '',
}: MarkdownRenderProps) {
  // 记忆化处理，避免重复渲染
  const memoizedContent = useMemo(() => content, [content]);

  return (
    <div className={`prose prose-sm max-w-none text-text ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 代码块渲染
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');
            const codeString = String(children).replace(/\n$/, '');

            // 行内代码
            if (inline) {
              return (
                <code
                  className="px-1.5 py-0.5 bg-gray-100 text-accent-600 rounded text-sm font-mono"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            // 代码块
            return (
              <div className="my-4 rounded-xl overflow-hidden">
                <div className="flex items-center justify-between px-4 py-2 bg-gray-800 text-gray-400 text-xs">
                  <span>{match ? match[1] : 'code'}</span>
                  <button
                    onClick={() => navigator.clipboard.writeText(codeString)}
                    className="flex items-center gap-1 hover:text-white transition-colors"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    复制
                  </button>
                </div>
                <SyntaxHighlighter
                  style={oneDark}
                  language={match ? match[1] : 'text'}
                  showLineNumbers={showLineNumbers}
                  customStyle={{
                    margin: 0,
                    padding: '1rem',
                    fontSize: '0.875rem',
                    lineHeight: '1.6',
                    background: '#1e1e1e',
                  }}
                >
                  {codeString}
                </SyntaxHighlighter>
              </div>
            );
          },

          // 标题样式
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-text mt-6 mb-4 pb-2 border-b border-gray-100">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-bold text-text mt-5 mb-3">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold text-text mt-4 mb-2">{children}</h3>
          ),

          // 段落
          p: ({ children }) => (
            <p className="my-3 text-text-secondary leading-relaxed">{children}</p>
          ),

          // 列表
          ul: ({ children }) => (
            <ul className="my-3 ml-6 list-disc space-y-1 text-text-secondary">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="my-3 ml-6 list-decimal space-y-1 text-text-secondary">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed">{children}</li>
          ),

          // 引用
          blockquote: ({ children }) => (
            <blockquote className="my-4 pl-4 border-l-4 border-primary-300 bg-primary-50/50 py-2 pr-4 rounded-r-lg text-text-secondary italic">
              {children}
            </blockquote>
          ),

          // 表格
          table: ({ children }) => (
            <div className="my-4 overflow-x-auto rounded-lg border border-gray-200">
              <table className="w-full text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-gray-50">{children}</thead>
          ),
          th: ({ children }) => (
            <th className="px-4 py-2 text-left font-medium text-text border-b border-gray-200">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-2 text-text-secondary border-b border-gray-100">
              {children}
            </td>
          ),

          // 链接
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:text-primary-700 hover:underline"
            >
              {children}
            </a>
          ),

          // 图片
          img: ({ src, alt }) => (
            <img
              src={src}
              alt={alt || ''}
              className="max-w-full rounded-lg my-4"
              loading="lazy"
            />
          ),

          // 分割线
          hr: () => <hr className="my-6 border-gray-200" />,

          // 加粗
          strong: ({ children }) => (
            <strong className="font-semibold text-text">{children}</strong>
          ),

          // 任务列表
          input: ({ type, checked }) => {
            if (type === 'checkbox') {
              return (
                <input
                  type="checkbox"
                  checked={checked}
                  readOnly
                  className="mr-2 rounded border-gray-300 text-primary-500 focus:ring-primary-500"
                />
              );
            }
            return null;
          },
        }}
      >
        {memoizedContent}
      </ReactMarkdown>
    </div>
  );
}
