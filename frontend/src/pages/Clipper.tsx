/**
 * 选材剪藏页面
 * 输入链接 → 抓取正文 → 自动归档到知识库
 * 支持书签小工具、关键词搜索、分类筛选、详情预览与删除
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import Button from '@/components/Common/Button';
import Input from '@/components/Common/Input';
import Modal from '@/components/Common/Modal';
import MarkdownRender from '@/components/MarkdownRender';
import { formatDate } from '@/utils/format';
import {
  buildBookmarklet,
  clipWebPage,
  deleteClipping,
  getClippingDetail,
  getClippings,
} from '@/api/clipper';
import type { Clipping, ClippingDetail } from '@/api/types';

// 常用分类，覆盖三条主线：专业变现 / 内容生产 / 个人成长
const CATEGORIES = ['技术', '行业', '管理', '产品', '写作', '学习'];

const PAGE_SIZE = 12;

export default function Clipper() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [items, setItems] = useState<Clipping[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const [url, setUrl] = useState('');
  const [category, setCategory] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [clipping, setClipping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [keyword, setKeyword] = useState('');
  const [filterCategory, setFilterCategory] = useState('');

  const [detail, setDetail] = useState<ClippingDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // 防止同一个 ?url= 被重复触发剪藏
  const autoClipDone = useRef(false);

  const fetchList = useCallback(
    async (targetPage: number, kw: string, cat: string) => {
      setLoading(true);
      setError(null);
      try {
        const res = await getClippings({
          page: targetPage,
          page_size: PAGE_SIZE,
          keyword: kw || undefined,
          category: cat || undefined,
        });
        setItems(res.items);
        setTotal(res.total);
        setPage(res.page);
      } catch (e) {
        setError(e instanceof Error ? e.message : '获取剪藏列表失败');
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const handleClip = useCallback(
    async (targetUrl: string) => {
      const value = targetUrl.trim();
      if (!value) {
        setError('请先输入要剪藏的链接');
        return;
      }

      setClipping(true);
      setError(null);
      setNotice(null);
      try {
        const res = await clipWebPage({
          url: value,
          category: category || undefined,
          tags: tagsInput
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean),
        });
        setNotice(`已归档：《${res.title}》，共 ${res.content_length} 字`);
        setUrl('');
        setTagsInput('');
        await fetchList(1, keyword, filterCategory);
      } catch (e) {
        setError(e instanceof Error ? e.message : '剪藏失败');
      } finally {
        setClipping(false);
      }
    },
    [category, tagsInput, keyword, filterCategory, fetchList]
  );

  // 首屏加载列表
  useEffect(() => {
    fetchList(1, '', '');
  }, [fetchList]);

  // 支持书签小工具带 ?url= 打开，自动剪藏
  useEffect(() => {
    const urlParam = searchParams.get('url');
    if (!urlParam || autoClipDone.current) return;
    autoClipDone.current = true;
    setUrl(urlParam);
    handleClip(urlParam);
    // 清掉 query，避免刷新后重复触发
    setSearchParams({}, { replace: true });
  }, [searchParams, setSearchParams, handleClip]);

  const handleSearch = () => {
    fetchList(1, keyword, filterCategory);
  };

  const handleCopyBookmarklet = async () => {
    try {
      await navigator.clipboard.writeText(buildBookmarklet());
      setNotice('书签代码已复制，请在浏览器新建书签并把代码粘贴到「网址」栏');
    } catch {
      setError('复制失败，请手动选中下方代码复制');
    }
  };

  const handleOpenDetail = async (id: number) => {
    setDetailLoading(true);
    try {
      const res = await getClippingDetail(id);
      setDetail(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : '获取详情失败');
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDelete = async (item: Clipping) => {
    if (!window.confirm(`确定删除《${item.title}》？知识库中的对应文档也会被删除。`)) return;
    try {
      await deleteClipping(item.id);
      await fetchList(page, keyword, filterCategory);
    } catch (e) {
      setError(e instanceof Error ? e.message : '删除失败');
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-6">
      {/* 剪藏输入区 */}
      <div className="bg-white rounded-2xl shadow-soft p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-text">剪藏一个网页</h2>
            <p className="text-sm text-text-tertiary mt-1">
              抓取正文并自动归档到「剪藏」知识库，可直接被知识库检索与写作引用
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={handleCopyBookmarklet}>
            复制书签小工具
          </Button>
        </div>

        <div className="flex flex-col md:flex-row gap-3">
          <div className="flex-1">
            <Input
              placeholder="粘贴文章链接，例如 https://mp.weixin.qq.com/s/xxxx"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleClip(url);
              }}
            />
          </div>
          <select
            className="h-10 px-3 border border-gray-200 rounded-lg text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary-100 focus:border-primary-400"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="">不分类</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <div className="md:w-56">
            <Input
              placeholder="标签，逗号分隔"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
            />
          </div>
          <Button onClick={() => handleClip(url)} loading={clipping}>
            剪藏
          </Button>
        </div>

        {notice && (
          <div className="mt-3 px-4 py-2.5 bg-green-50 text-green-700 text-sm rounded-lg">
            {notice}
          </div>
        )}
        {error && (
          <div className="mt-3 px-4 py-2.5 bg-danger-50 text-danger-600 text-sm rounded-lg">
            {error}
          </div>
        )}
      </div>

      {/* 筛选区 */}
      <div className="flex flex-col md:flex-row md:items-center gap-3">
        <div className="flex-1 max-w-md">
          <Input
            placeholder="搜索标题 / 摘要 / 标签"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSearch();
            }}
          />
        </div>
        <select
          className="h-10 px-3 border border-gray-200 rounded-lg text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary-100 focus:border-primary-400"
          value={filterCategory}
          onChange={(e) => {
            setFilterCategory(e.target.value);
            fetchList(1, keyword, e.target.value);
          }}
        >
          <option value="">全部分类</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <Button variant="outline" onClick={handleSearch}>
          搜索
        </Button>
        <div className="md:ml-auto text-sm text-text-tertiary">共 {total} 条</div>
      </div>

      {/* 列表区 */}
      {loading ? (
        <div className="text-center py-16 text-text-tertiary">加载中...</div>
      ) : items.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-soft p-16 text-center">
          <div className="text-4xl mb-3">✂️</div>
          <p className="text-text-secondary">还没有剪藏内容</p>
          <p className="text-sm text-text-tertiary mt-1">
            粘贴一个链接开始，或把「书签小工具」拖到浏览器书签栏
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-2xl shadow-soft p-5 flex flex-col hover:shadow-large transition-shadow"
            >
              <div className="flex items-start gap-2 mb-2">
                <span
                  className={`flex-shrink-0 px-2 py-0.5 rounded text-xs ${
                    item.status === 'ready'
                      ? 'bg-green-100 text-green-600'
                      : 'bg-danger-100 text-danger-600'
                  }`}
                >
                  {item.status === 'ready' ? '已归档' : '失败'}
                </span>
                {item.category && (
                  <span className="flex-shrink-0 px-2 py-0.5 rounded text-xs bg-primary-100 text-primary-600">
                    {item.category}
                  </span>
                )}
                <span className="text-xs text-text-tertiary ml-auto flex-shrink-0">
                  {item.content_length} 字
                </span>
              </div>

              <button
                className="text-left font-medium text-text hover:text-primary-600 line-clamp-2"
                onClick={() => handleOpenDetail(item.id)}
              >
                {item.title}
              </button>

              <p className="text-sm text-text-tertiary mt-2 line-clamp-3 flex-1">
                {item.error_msg || item.summary}
              </p>

              <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-50">
                <span className="text-xs text-text-tertiary truncate max-w-[60%]">
                  {item.site_name || '未知站点'} · {formatDate(item.created_at)}
                </span>
                <div className="flex items-center gap-1">
                  <button
                    className="p-1.5 rounded-lg text-text-tertiary hover:text-primary-600 hover:bg-gray-50"
                    title="查看详情"
                    onClick={() => handleOpenDetail(item.id)}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                  <button
                    className="p-1.5 rounded-lg text-text-tertiary hover:text-danger-500 hover:bg-gray-50"
                    title="删除"
                    onClick={() => handleDelete(item)}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => fetchList(page - 1, keyword, filterCategory)}
          >
            上一页
          </Button>
          <span className="text-sm text-text-secondary">
            {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => fetchList(page + 1, keyword, filterCategory)}
          >
            下一页
          </Button>
        </div>
      )}

      {/* 详情弹窗 */}
      <Modal
        visible={!!detail || detailLoading}
        title={detail?.title || '加载中...'}
        onClose={() => setDetail(null)}
        width={820}
        footer={
          detail ? (
            <div className="flex items-center justify-between w-full">
              <a
                href={detail.url}
                target="_blank"
                rel="noreferrer"
                className="text-sm text-primary-600 hover:underline truncate max-w-[60%]"
              >
                查看原文
              </a>
              <div className="flex items-center gap-2">
                <span className="text-xs text-text-tertiary">
                  {detail.site_name} · {formatDate(detail.created_at)}
                </span>
                <Button variant="outline" size="sm" onClick={() => setDetail(null)}>
                  关闭
                </Button>
              </div>
            </div>
          ) : null
        }
      >
        {detailLoading && !detail ? (
          <div className="py-12 text-center text-text-tertiary">加载中...</div>
        ) : detail ? (
          <div className="max-h-[60vh] overflow-y-auto">
            {detail.tags && (
              <div className="flex flex-wrap gap-2 mb-4">
                {detail.tags.split(',').filter(Boolean).map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-0.5 rounded bg-gray-100 text-text-secondary text-xs"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}
            <MarkdownRender content={detail.content_md} />
          </div>
        ) : null}
      </Modal>
    </div>
  );
}
