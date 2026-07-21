/**
 * 技术专家组相关 API
 */

import { get, post } from './index';
import type {
  ExpertSession,
  ExpertMessage,
  Expert,
  CreateSessionRequest,
  SendMessageRequest,
  PhaseActionRequest,
  SwitchExpertRequest,
  StateTransition,
  PhaseProgress,
  PaginatedResponse,
  PaginationParams,
  ExpertRole,
} from './types';

/**
 * 获取专家列表
 */
export function getExperts(): Promise<Expert[]> {
  return get<Expert[]>('/tech-experts/experts');
}

/**
 * 获取会话列表
 * @param params 分页参数
 */
export function getSessions(
  params?: PaginationParams
): Promise<PaginatedResponse<ExpertSession>> {
  return get<PaginatedResponse<ExpertSession>>('/tech-experts/sessions', params);
}

/**
 * 获取会话详情
 * @param sessionId 会话 ID
 */
export function getSession(sessionId: number): Promise<ExpertSession> {
  return get<ExpertSession>(`/tech-experts/sessions/${sessionId}`);
}

/**
 * 创建会话
 * @param data 会话信息
 */
export function createSession(data: CreateSessionRequest): Promise<ExpertSession> {
  return post<ExpertSession>('/tech-experts/sessions', data);
}

/**
 * 删除会话
 * @param sessionId 会话 ID
 */
export function deleteSession(sessionId: number): Promise<void> {
  return post<void>(`/tech-experts/sessions/${sessionId}/delete`);
}

/**
 * 获取会话消息列表
 * @param sessionId 会话 ID
 * @param params 分页参数
 */
export function getMessages(
  sessionId: number,
  params?: PaginationParams
): Promise<PaginatedResponse<ExpertMessage>> {
  return get<PaginatedResponse<ExpertMessage>>(
    `/tech-experts/sessions/${sessionId}/messages`,
    params
  );
}

/**
 * 发送消息（普通模式）
 * @param data 消息数据
 */
export function sendMessage(data: SendMessageRequest): Promise<ExpertMessage> {
  return post<ExpertMessage>('/tech-experts/messages', data);
}

/**
 * 获取 SSE 流式响应的 URL
 * @param sessionId 会话 ID
 * @param content 消息内容
 * @param expertRole 专家角色
 */
export function getSSEUrl(
  sessionId: number,
  content: string,
  expertRole?: ExpertRole
): string {
  const baseUrl = import.meta.env.VITE_SSE_BASE_URL || import.meta.env.VITE_API_BASE_URL;
  const token = localStorage.getItem('token') || '';
  const params = new URLSearchParams({
    session_id: String(sessionId),
    content,
    ...(expertRole && { expert_role: expertRole }),
    token,
  });
  return `${baseUrl}/tech-experts/stream?${params.toString()}`;
}

/**
 * 阶段操作（确认/回退）
 * @param data 操作数据
 */
export function phaseAction(data: PhaseActionRequest): Promise<StateTransition> {
  return post<StateTransition>('/tech-experts/phase-action', data);
}

/**
 * 切换专家
 * @param data 切换专家数据
 */
export function switchExpert(data: SwitchExpertRequest): Promise<ExpertSession> {
  return post<ExpertSession>('/tech-experts/switch-expert', data);
}

/**
 * 获取阶段进度
 * @param sessionId 会话 ID
 */
export function getPhaseProgress(sessionId: number): Promise<PhaseProgress[]> {
  return get<PhaseProgress[]>(`/tech-experts/sessions/${sessionId}/progress`);
}

/**
 * 获取状态转换历史
 * @param sessionId 会话 ID
 */
export function getStateTransitions(sessionId: number): Promise<StateTransition[]> {
  return get<StateTransition[]>(`/tech-experts/sessions/${sessionId}/transitions`);
}
