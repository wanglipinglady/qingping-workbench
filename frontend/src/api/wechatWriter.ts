/**
 * 微信公众号写作助手相关 API
 */

import { get, post, put, del, aiPost } from './index';
import type {
  WriterSession,
  WriterOutput,
  WriterMaterial,
  PaginatedResponse,
  PaginationParams,
} from './types';

// ==================== 会话相关 ====================

export interface CreateWriterSessionRequest {
  topic: string;
  title?: string;
}

export interface UpdateWriterSessionRequest {
  title?: string;
  confirmed_topic?: string;
  status?: 'active' | 'completed' | 'archived';
}

export interface StateOperationRequest {
  action: 'confirm' | 'regenerate' | 'rollback' | 'switch_expert';
  target_state?: string;
  feedback?: string;
  expert_type?: string;
}

/**
 * 获取会话列表
 */
export function getWriterSessions(
  params?: PaginationParams & { status?: string; keyword?: string }
): Promise<PaginatedResponse<WriterSession>> {
  return get<PaginatedResponse<WriterSession>>('/wechat-writer/sessions', params);
}

/**
 * 获取会话详情
 */
export function getWriterSession(sessionId: number): Promise<WriterSession> {
  return get<WriterSession>(`/wechat-writer/sessions/${sessionId}`);
}

/**
 * 创建会话
 */
export function createWriterSession(
  data: CreateWriterSessionRequest
): Promise<WriterSession> {
  return post<WriterSession>('/wechat-writer/sessions', data);
}

/**
 * 更新会话
 */
export function updateWriterSession(
  sessionId: number,
  data: UpdateWriterSessionRequest
): Promise<WriterSession> {
  return put<WriterSession>(`/wechat-writer/sessions/${sessionId}`, data);
}

/**
 * 删除会话
 */
export function deleteWriterSession(sessionId: number): Promise<void> {
  return del<void>(`/wechat-writer/sessions/${sessionId}`);
}

// ==================== 状态操作 ====================

/**
 * 开始写作（从 idle 进入选题确认）- AI 长超时
 */
export function startWriting(sessionId: number): Promise<{
  from_state: string;
  to_state: string;
  expert: string;
  response: string;
}> {
  return aiPost(`/wechat-writer/sessions/${sessionId}/start`);
}

/**
 * 确认当前状态，进入下一步 - AI 长超时
 * 确认后会自动触发下一状态的 AI 生成，返回 response 字段
 */
export function confirmState(sessionId: number): Promise<{
  from_state: string;
  to_state: string;
  expert?: string;
  response: string;
  message: string;
}> {
  return aiPost(`/wechat-writer/sessions/${sessionId}/confirm`);
}

/**
 * 重新生成当前步骤的输出 - AI 长超时
 */
export function regenerateOutput(
  sessionId: number,
  feedback?: string
): Promise<{
  state: string;
  expert: string;
  version: number;
  feedback: string | null;
  response: string;
}> {
  return aiPost(`/wechat-writer/sessions/${sessionId}/regenerate`, {
    action: 'regenerate',
    feedback,
  });
}

/**
 * 回退到指定状态
 */
export function rollbackToState(
  sessionId: number,
  targetState: string,
  feedback?: string
): Promise<{
  from_state: string;
  to_state: string;
  reason: string;
  message: string;
}> {
  return aiPost(`/wechat-writer/sessions/${sessionId}/rollback`, {
    action: 'rollback',
    target_state: targetState,
    feedback,
  });
}

// ==================== 资料卡片 ====================

/**
 * 获取资料卡片列表
 */
export function getMaterials(
  sessionId: number,
  params?: { source_type?: string; is_useful?: boolean }
): Promise<WriterMaterial[]> {
  return get<WriterMaterial[]>(`/wechat-writer/sessions/${sessionId}/materials`, params);
}

// ==================== 输出版本 ====================

/**
 * 获取输出版本列表
 */
export function getOutputs(
  sessionId: number,
  params?: { step?: string }
): Promise<WriterOutput[]> {
  return get<WriterOutput[]>(`/wechat-writer/sessions/${sessionId}/outputs`, params);
}

// ==================== 导出文章 ====================

/**
 * 导出文章为 Markdown 或 TXT 文件
 *
 * 认证方式：token 同时放在 URL query 参数和 Authorization header 中，
 * 确保无论哪种方式都能通过后端认证。
 *
 * 错误处理：非 2xx 响应会解析 JSON 错误信息并 alert 提示用户，
 * 不会把错误 JSON 当成文件下载。
 */
export function exportArticle(sessionId: number, format: 'markdown' | 'txt' = 'markdown'): void {
  const token = localStorage.getItem('token');
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';

  // 把 token 放到 URL query 中（支持浏览器直接打开链接下载）
  const queryToken = token ? `&token=${encodeURIComponent(token)}` : '';
  const url = `${baseUrl}/wechat-writer/sessions/${sessionId}/export?format=${format}${queryToken}`;

  fetch(url, {
    headers: token ? { 'Authorization': `Bearer ${token}` } : {},
  })
    .then(async (res) => {
      if (!res.ok) {
        // 解析后端返回的错误 JSON
        const errorData = await res.json().catch(() => ({ message: '导出失败' }));
        const errorMsg = errorData.message || errorData.detail || '导出失败';
        alert(`导出失败：${errorMsg}`);
        throw new Error(errorMsg);
      }
      const blob = await res.blob();
      const contentDisposition = res.headers.get('Content-Disposition');
      return { blob, contentDisposition };
    })
    .then(({ blob, contentDisposition }) => {
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      // 从 Content-Disposition 提取文件名
      let filename = 'article.md';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename\*=UTF-8''(.+)/);
        if (match) {
          filename = decodeURIComponent(match[1]);
        }
      }
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(downloadUrl);
    })
    .catch((error) => {
      // 已 alert 过的错误不再重复提示
      console.error('导出文章失败:', error);
    });
}
