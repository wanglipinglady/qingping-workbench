/**
 * 技术专家组相关 API
 */

import { get, post, del } from './index';
import type {
  ExpertSession,
  ExpertMessage,
  Expert,
  CreateSessionRequest,
  SendMessageRequest,
  SwitchExpertRequest,
  RollbackRequest,
  StateInfo,
  PaginationParams,
} from './types';

/** 会话列表响应（后端返回 {items, total}，无分页元数据） */
export interface SessionListResponse {
  items: ExpertSession[];
  total: number;
}

/**
 * 获取专家列表
 */
export function getExperts(): Promise<Expert[]> {
  return get<Expert[]>('/tech-experts/experts');
}

/**
 * 获取会话列表
 */
export function getSessions(params?: PaginationParams): Promise<SessionListResponse> {
  return get<SessionListResponse>('/tech-experts/sessions', params);
}

/**
 * 获取会话详情
 */
export function getSession(sessionId: number): Promise<ExpertSession> {
  return get<ExpertSession>(`/tech-experts/sessions/${sessionId}`);
}

/**
 * 创建会话
 */
export function createSession(data: CreateSessionRequest): Promise<ExpertSession> {
  return post<ExpertSession>('/tech-experts/sessions', data);
}

/**
 * 删除会话
 */
export function deleteSession(sessionId: number): Promise<void> {
  return del<void>(`/tech-experts/sessions/${sessionId}`);
}

/**
 * 获取会话消息列表（后端返回纯数组，非分页）
 */
export function getMessages(sessionId: number): Promise<ExpertMessage[]> {
  return get<ExpertMessage[]>(`/tech-experts/sessions/${sessionId}/messages`);
}

/**
 * 发送消息（同步模式）
 */
export function sendMessage(data: SendMessageRequest): Promise<unknown> {
  return post<unknown>(`/tech-experts/sessions/${data.session_id}/chat`, {
    message: data.message,
  });
}

/**
 * 获取流式对话接口地址
 */
export function getChatStreamUrl(sessionId: number): string {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
  return `${baseUrl}/tech-experts/sessions/${sessionId}/chat/stream`;
}

/**
 * 确认当前状态，进入下一状态
 */
export function confirmState(sessionId: number): Promise<unknown> {
  return post<unknown>(`/tech-experts/sessions/${sessionId}/state/confirm`);
}

/**
 * 回退到指定状态
 */
export function rollbackState(data: RollbackRequest): Promise<unknown> {
  return post<unknown>(`/tech-experts/sessions/${data.session_id}/state/rollback`, {
    target_state: data.target_state,
    reason: data.reason,
  });
}

/**
 * 切换专家
 */
export function switchExpert(data: SwitchExpertRequest): Promise<unknown> {
  return post<unknown>(`/tech-experts/sessions/${data.session_id}/state/switch`, {
    expert_type: data.expert_type,
  });
}

/**
 * 获取当前状态信息
 */
export function getStateInfo(sessionId: number): Promise<StateInfo> {
  return get<StateInfo>(`/tech-experts/sessions/${sessionId}/state`);
}
