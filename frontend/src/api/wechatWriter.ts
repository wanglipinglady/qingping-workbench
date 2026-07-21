/**
 * 微信公众号写作助手相关 API
 */

import { get, post, put, del } from './index';
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
 * 开始写作（从 idle 进入选题确认）
 */
export function startWriting(sessionId: number): Promise<{
  from_state: string;
  to_state: string;
  expert: string;
  response: string;
}> {
  return post(`/wechat-writer/sessions/${sessionId}/start`);
}

/**
 * 确认当前状态，进入下一步
 */
export function confirmState(sessionId: number): Promise<{
  from_state: string;
  to_state: string;
  message: string;
}> {
  return post(`/wechat-writer/sessions/${sessionId}/confirm`);
}

/**
 * 重新生成当前步骤的输出
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
  return post(`/wechat-writer/sessions/${sessionId}/regenerate`, {
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
  return post(`/wechat-writer/sessions/${sessionId}/rollback`, {
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
