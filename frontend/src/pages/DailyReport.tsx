/**
 * 学习日报页面
 * 左侧日期列表，右侧日报正文；支持手动生成 / 重新生成 / 删除
 */

import { useCallback, useEffect, useState } from 'react';
import Button from '@/components/Common/Button';
import MarkdownRender from '@/components/MarkdownRender';
import { formatDate } from '@/utils/format';
import { deleteReport, generateReport, getReport, getReports } from '@/api/dailyReports';
import type { DailyReport, DailyReportDetail } from '@/api/types';

/** 今天的本地日期 YYYY-MM-DD */
function today(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export default function DailyReport() {
  const [reports, setReports] = useState<DailyReport[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [detail, setDetail] = useState<DailyReportDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [targetDate, setTargetDate] = useState(today());
  const [error, setError] = useState<string | null>(null);

  const fetchList = useCallback(async (preferDate?: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getReports({ page: 1, page_size: 60 });
      setReports(res.items);
      if (res.items.length > 0) {
        const next =
          (preferDate && res.items.find((r) => r.report_date === preferDate)?.report_date) ||
          res.items[0].report_date;
        setSelectedDate(next);
      } else {
        setSelectedDate('');
        setDetail(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '获取日报列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDetail = useCallback(async (date: string) => {
    if (!date) return;
    setDetailLoading(true);
    setError(null);
    try {
      setDetail(await getReport(date));
    } catch (e) {
      setDetail(null);
      setError(e instanceof Error ? e.message : '获取日报失败');
    } finally {
      setDetailLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  useEffect(() => {
    fetchDetail(selectedDate);
  }, [selectedDate, fetchDetail]);

  const handleGenerate = async (force: boolean) => {
    setGenerating(true);
    setError(null);
    try {
      const res = await generateReport({ report_date: targetDate, force });
      await fetchList(res.report_date);
      setDetail(res);
      setSelectedDate(res.report_date);
    } catch (e) {
      setError(e instanceof Error ? e.message : '生成日报失败');
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (date: string) => {
    if (!window.confirm(`确定删除 ${date} 的日报？`)) return;
    try {
      await deleteReport(date);
      await fetchList();
    } catch (e) {
      setError(e instanceof Error ? e.message : '删除失败');
    }
  };

  const stats = detail?.stats;

  return (
    <div className="space-y-6">
      {/* 生成区 */}
      <div className="bg-white rounded-2xl shadow-soft p-6">
        <div className="flex flex-col md:flex-row md:items-end gap-4">
          <div>
            <h2 className="text-lg font-semibold text-text">生成学习日报</h2>
            <p className="text-sm text-text-tertiary mt-1">
              聚合当日剪藏、知识库新增、技术对话与写作记录，自动整理成可执行的日报
            </p>
          </div>
          <div className="md:ml-auto flex items-end gap-3">
            <div>
              <label className="block text-xs text-text-tertiary mb-1">日期</label>
              <input
                type="date"
                className="h-10 px-3 border border-gray-200 rounded-lg text-sm text-text bg-white focus:outline-none focus:ring-2 focus:ring-primary-100 focus:border-primary-400"
                value={targetDate}
                max={today()}
                onChange={(e) => setTargetDate(e.target.value)}
              />
            </div>
            <Button onClick={() => handleGenerate(false)} loading={generating}>
              生成日报
            </Button>
            <Button variant="outline" onClick={() => handleGenerate(true)} disabled={generating}>
              强制重新生成
            </Button>
          </div>
        </div>

        {error && (
          <div className="mt-3 px-4 py-2.5 bg-danger-50 text-danger-600 text-sm rounded-lg">
            {error}
          </div>
        )}
        {detail?.generated_by === 'fallback' && (
          <div className="mt-3 px-4 py-2.5 bg-yellow-50 text-yellow-700 text-sm rounded-lg">
            本次为规则兜底日报（模型不可用）：{detail.error_msg || '未知原因'}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 日期列表 */}
        <div className="bg-white rounded-2xl shadow-soft p-4 lg:col-span-1">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-text">历史日报</h3>
            <span className="text-xs text-text-tertiary">{reports.length} 份</span>
          </div>
          {loading ? (
            <div className="py-8 text-center text-sm text-text-tertiary">加载中...</div>
          ) : reports.length === 0 ? (
            <div className="py-8 text-center text-sm text-text-tertiary">
              还没有日报
            </div>
          ) : (
            <div className="space-y-1 max-h-[60vh] overflow-y-auto">
              {reports.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setSelectedDate(r.report_date)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors ${
                    selectedDate === r.report_date
                      ? 'bg-primary-50 text-primary-600'
                      : 'text-text-secondary hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{r.report_date}</span>
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded ${
                        r.generated_by === 'llm'
                          ? 'bg-green-100 text-green-600'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}
                    >
                      {r.generated_by === 'llm' ? 'AI' : '兜底'}
                    </span>
                  </div>
                  <div className="text-xs text-text-tertiary mt-0.5">
                    剪藏 {r.stats.clips} · 文档 {r.stats.documents} · 对话{' '}
                    {r.stats.expert_messages + r.stats.writer_messages}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 日报正文 */}
        <div className="bg-white rounded-2xl shadow-soft p-6 lg:col-span-3">
          {detailLoading ? (
            <div className="py-16 text-center text-text-tertiary">加载中...</div>
          ) : !detail ? (
            <div className="py-16 text-center">
              <div className="text-4xl mb-3">📅</div>
              <p className="text-text-secondary">还没有选中日报</p>
              <p className="text-sm text-text-tertiary mt-1">
                选择日期后点击「生成日报」，或从左侧历史中选择
              </p>
            </div>
          ) : (
            <div>
              <div className="flex flex-wrap items-center gap-3 pb-4 mb-4 border-b border-gray-50">
                <h3 className="text-lg font-semibold text-text">{detail.report_date} 学习日报</h3>
                <span className="text-xs text-text-tertiary">
                  {stats && `剪藏 ${stats.clips} · 知识库新增 ${stats.documents} · 技术对话 ${stats.expert_messages} · 写作 ${stats.writer_messages}`}
                </span>
                <span className="text-xs text-text-tertiary ml-auto">
                  更新于 {formatDate(detail.updated_at)}
                </span>
                <button
                  className="p-1.5 rounded-lg text-text-tertiary hover:text-danger-500 hover:bg-gray-50"
                  title="删除该日报"
                  onClick={() => handleDelete(detail.report_date)}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
              <div className="max-h-[65vh] overflow-y-auto">
                <MarkdownRender content={detail.content_md} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
