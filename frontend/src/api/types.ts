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
  doc_count: number;
  user_id: number;
  created_at: string;
  updated_at: string;
}

/** 创建知识库请求 */
export interface CreateKnowledgeBaseRequest {
  name: string;
  description?: string;
}

/** 更新知识库请求 */
export interface UpdateKnowledgeBaseRequest {
  name?: string;
  description?: string;
}

/** 文档 */
export interface Document {
  id: number;
  kb_id: number;
  filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  status: 'processing' | 'ready' | 'failed';
  created_at: string;
}

/** 搜索结果 */
export interface SearchResult {
  id: string;
  document_id?: number;
  document_name?: string;
  content: string;
  score: number;
  distance?: number;
  chunk_index?: number;
}

/** 搜索请求 */
export interface SearchRequest {
  query: string;
  knowledge_base_id?: number;
  top_k?: number;
}

/** 搜索响应 */
export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

// ==================== 技术专家组相关类型 ====================

/** 专家类型 */
export type ExpertType = 'architect' | 'coder' | 'reviewer' | 'tester';

/** 技术专家状态 */
export type TechExpertState = 'idle' | 'arch_design' | 'code_impl' | 'code_review' | 'testing' | 'done';

/** 会话状态 */
export type SessionStatus = 'active' | 'completed' | 'archived';

/** 专家信息 */
export interface Expert {
  type: ExpertType;
  name: string;
  icon: string;
  color: string;
  description: string;
  state?: string;
}

/** 专家会话 */
export interface ExpertSession {
  id: number;
  title: string;
  current_state: TechExpertState;
  current_state_label?: string;
  iteration_count: number;
  status: SessionStatus;
  total_tokens?: number;
  user_id?: number;
  max_iterations?: number;
  acceptance_criteria?: Record<string, unknown> | null;
  created_at?: string;
  updated_at?: string;
}

/** 专家消息 */
export interface ExpertMessage {
  id: number;
  session_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  expert_type?: ExpertType | null;
  state_label?: string | null;
  iteration: number;
  token_usage?: number;
  is_streaming?: boolean;
  created_at: string;
}

/** 状态信息 */
export interface StateInfo {
  current_state: TechExpertState;
  current_state_label: string;
  current_expert?: ExpertType | null;
  current_expert_name?: string | null;
  iteration: number;
  can_confirm: boolean;
  can_rollback_to: TechExpertState[];
  pause_for_human: boolean;
}

/** 创建会话请求 */
export interface CreateSessionRequest {
  title?: string;
  initial_message?: string;
}

/** 发送消息请求 */
export interface SendMessageRequest {
  session_id: number;
  message: string;
}

/** 切换专家请求 */
export interface SwitchExpertRequest {
  session_id: number;
  expert_type: ExpertType;
}

/** 回退请求 */
export interface RollbackRequest {
  session_id: number;
  target_state: TechExpertState;
  reason?: string;
}

// ==================== 选材剪藏相关类型 ====================

/** 剪藏记录 */
export interface Clipping {
  id: number;
  url: string;
  title: string;
  site_name: string;
  author: string;
  summary: string;
  tags: string;
  category: string;
  content_length: number;
  kb_id: number;
  document_id?: number | null;
  status: 'ready' | 'failed';
  error_msg?: string | null;
  created_at: string;
}

/** 剪藏详情（含正文） */
export interface ClippingDetail extends Clipping {
  content_md: string;
}

/** 剪藏请求 */
export interface ClipRequest {
  url: string;
  kb_id?: number;
  category?: string;
  tags?: string[];
}

/** 剪藏列表响应 */
export interface ClippingListResponse {
  items: Clipping[];
  total: number;
  page: number;
  page_size: number;
}

// ==================== 学习日报相关类型 ====================

/** 日报数据统计 */
export interface ReportStats {
  clips: number;
  clip_titles: string[];
  documents: number;
  expert_messages: number;
  writer_messages: number;
  writer_outputs: number;
}

/** 学习日报（列表项） */
export interface DailyReport {
  id: number;
  report_date: string;
  stats: ReportStats;
  generated_by: 'llm' | 'fallback';
  error_msg?: string | null;
  created_at: string;
  updated_at: string;
}

/** 学习日报详情 */
export interface DailyReportDetail extends DailyReport {
  content_md: string;
}

/** 日报列表响应 */
export interface DailyReportListResponse {
  items: DailyReport[];
  total: number;
  page: number;
  page_size: number;
}

/** 生成日报请求 */
export interface GenerateReportRequest {
  report_date?: string;
  force?: boolean;
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
  obsidian_folder?: string;
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
