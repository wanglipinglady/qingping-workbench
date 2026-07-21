/**
 * API 类型定义
 * 定义所有 API 请求和响应的数据结构
 */

// ==================== 通用类型 ====================

/** 通用分页请求参数 */
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

/** 通用分页响应 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** 通用 API 响应 */
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

// ==================== 用户相关类型 ====================

/** 用户信息 */
export interface User {
  id: number;
  username: string;
  email?: string;
  nickname?: string;
  avatar?: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** 登录请求 */
export interface LoginRequest {
  username: string;
  password: string;
}

/** 登录响应 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

/** 注册请求 */
export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
  nickname?: string;
}

// ==================== 知识库相关类型 ====================

/** 知识库 */
export interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
  document_count: number;
  is_public: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

/** 创建知识库请求 */
export interface CreateKnowledgeBaseRequest {
  name: string;
  description?: string;
  is_public?: boolean;
}

/** 更新知识库请求 */
export interface UpdateKnowledgeBaseRequest {
  name?: string;
  description?: string;
  is_public?: boolean;
}

/** 文档 */
export interface Document {
  id: number;
  knowledge_base_id: number;
  title: string;
  file_name: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

/** 搜索结果 */
export interface SearchResult {
  id: number;
  document_id: number;
  document_title: string;
  content: string;
  similarity: number;
  chunk_index: number;
}

/** 搜索请求 */
export interface SearchRequest {
  query: string;
  knowledge_base_id?: number;
  top_k?: number;
}

// ==================== 技术专家组相关类型 ====================

/** 专家角色 */
export type ExpertRole = 'architect' | 'developer' | 'reviewer' | 'tester';

/** 专家阶段 */
export type ExpertPhase = 'architecture' | 'implementation' | 'review' | 'testing';

/** 会话状态 */
export type SessionStatus = 'active' | 'completed' | 'archived';

/** 专家信息 */
export interface Expert {
  role: ExpertRole;
  name: string;
  avatar: string;
  description: string;
  color: string;
}

/** 专家会话 */
export interface ExpertSession {
  id: number;
  title: string;
  current_phase: ExpertPhase;
  current_iteration: number;
  status: SessionStatus;
  knowledge_base_id?: number;
  created_by: number;
  created_at: string;
  updated_at: string;
}

/** 专家消息 */
export interface ExpertMessage {
  id: number;
  session_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  expert_role?: ExpertRole;
  expert_name?: string;
  phase: ExpertPhase;
  iteration: number;
  is_streaming?: boolean;
  created_at: string;
}

/** 状态转换记录 */
export interface StateTransition {
  id: number;
  session_id: number;
  from_phase: ExpertPhase;
  to_phase: ExpertPhase;
  iteration: number;
  action: 'confirm' | 'rollback' | 'switch_expert';
  created_at: string;
}

/** 创建会话请求 */
export interface CreateSessionRequest {
  title: string;
  knowledge_base_id?: number;
}

/** 发送消息请求 */
export interface SendMessageRequest {
  session_id: number;
  content: string;
  expert_role?: ExpertRole;
}

/** 阶段操作请求 */
export interface PhaseActionRequest {
  session_id: number;
  action: 'confirm' | 'rollback';
  feedback?: string;
}

/** 切换专家请求 */
export interface SwitchExpertRequest {
  session_id: number;
  expert_role: ExpertRole;
}

/** 阶段进度 */
export interface PhaseProgress {
  phase: ExpertPhase;
  status: 'completed' | 'current' | 'pending';
  label: string;
}

// ==================== 微信公众号写作助手相关类型 ====================

/** 写作状态 */
export type WriterState = 'idle' | 'topic_confirm' | 'research' | 'outline' | 'draft' | 'polish' | 'done';

/** 写作会话 */
export interface WriterSession {
  id: number;
  user_id: number;
  title: string;
  topic: string;
  confirmed_topic?: string;
  current_state: WriterState;
  iteration_count: number;
  status: 'active' | 'completed' | 'archived';
  total_tokens: number;
  obsidian_sync_time?: string;
  material_count?: number;
  message_count?: number;
  output_count?: number;
  created_at: string;
  updated_at: string;
}

/** 写作资料卡片 */
export interface WriterMaterial {
  id: number;
  session_id: number;
  source_type: 'obsidian' | 'knowledge_base' | 'web';
  title: string;
  url?: string;
  core_idea?: string;
  useful_snippets?: string;
  credibility_score: number;
  suggested_usage?: string;
  is_useful: boolean;
  tags?: string;
  created_at: string;
}

/** 写作输出 */
export interface WriterOutput {
  id: number;
  session_id: number;
  step: 'topic' | 'research' | 'outline' | 'draft' | 'polish';
  content_type: 'analysis' | 'materials' | 'outline' | 'draft' | 'final';
  content: string;
  version: number;
  is_confirmed: boolean;
  feedback?: string;
  created_at: string;
}

/** 写作消息 */
export interface WriterMessage {
  id: number;
  session_id: number;
  role: 'user' | 'assistant' | 'system';
  expert_type?: string;
  state_label?: string;
  iteration: number;
  content: string;
  token_usage: number;
  is_streaming?: boolean;
  created_at: string;
}

// ==================== 统计相关类型 ====================

/** 首页统计数据 */
export interface DashboardStats {
  knowledge_base_count: number;
  document_count: number;
  conversation_count: number;
  api_call_count: number;
}

/** 最近访问记录 */
export interface RecentVisit {
  id: number;
  type: 'knowledge_base' | 'session';
  title: string;
  visited_at: string;
}
