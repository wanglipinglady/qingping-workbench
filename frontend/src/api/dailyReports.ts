/**
 * 学习日报相关 API
 */

import { get, post, del } from './index';
import type {
  DailyReportDetail,
  DailyReportListResponse,
  GenerateReportRequest,
} from './types';

/**
 * 生成（或覆盖）指定日期的日报
 */
export function generateReport(data: GenerateReportRequest = {}): Promise<DailyReportDetail> {
  return post<DailyReportDetail>('/daily-reports/generate', data);
}

/**
 * 获取日报列表（不含正文）
 */
export function getReports(
  params?: { page?: number; page_size?: number }
): Promise<DailyReportListResponse> {
  return get<DailyReportListResponse>('/daily-reports', params);
}

/**
 * 按日期获取日报详情
 * @param reportDate YYYY-MM-DD
 */
export function getReport(reportDate: string): Promise<DailyReportDetail> {
  return get<DailyReportDetail>(`/daily-reports/${reportDate}`);
}

/**
 * 删除指定日期的日报
 */
export function deleteReport(reportDate: string): Promise<void> {
  return del<void>(`/daily-reports/${reportDate}`);
}
