/**
 * 技术专家组状态管理
 * 管理会话列表、当前会话、消息列表、阶段进度等
 */

import { create } from 'zustand';
import {
  getSessions,
  getSession,
  createSession,
  deleteSession,
  getMessages,
  sendMessage,
  phaseAction,
  switchExpert,
  getPhaseProgress,
  getExperts,
} from '@/api/techExperts';
import type {
  ExpertSession,
  ExpertMessage,
  Expert,
  CreateSessionRequest,
  SendMessageRequest,
  PhaseActionRequest,
  SwitchExpertRequest,
  PhaseProgress,
  ExpertRole,
  ExpertPhase,
} from '@/api/types';

// ==================== 状态类型定义 ====================

interface TechExpertsState {
  /** 会话列表 */
  sessions: ExpertSession[];
  /** 当前会话 */
  currentSession: ExpertSession | null;
  /** 消息列表 */
  messages: ExpertMessage[];
  /** 专家列表 */
  experts: Expert[];
  /** 阶段进度 */
  phaseProgress: PhaseProgress[];
  /** 当前专家角色 */
  currentExpertRole: ExpertRole;
  /** 是否正在加载 */
  loading: {
    sessions: boolean;
    messages: boolean;
    send: boolean;
    phaseAction: boolean;
    stream: boolean;
  };
  /** 错误信息 */
  error: string | null;
  /** 流式输出当前消息索引 */
  streamingMessageIndex: number | null;
  /** 分页信息 */
  pagination: {
    sessions: { page: number; pageSize: number; total: number };
    messages: { page: number; pageSize: number; total: number };
  };
}

interface TechExpertsActions {
  /** 获取会话列表 */
  fetchSessions: (page?: number, pageSize?: number) => Promise<void>;
  /** 获取会话详情 */
  fetchSession: (sessionId: number) => Promise<void>;
  /** 创建会话 */
  createSessionItem: (data: CreateSessionRequest) => Promise<ExpertSession>;
  /** 删除会话 */
  deleteSessionItem: (sessionId: number) => Promise<void>;
  /** 设置当前会话 */
  setCurrentSession: (session: ExpertSession | null) => void;
  /** 获取消息列表 */
  fetchMessages: (sessionId: number, page?: number, pageSize?: number) => Promise<void>;
  /** 发送消息 */
  send: (data: SendMessageRequest) => Promise<ExpertMessage>;
  /** 添加用户消息（乐观更新） */
  addUserMessage: (content: string) => void;
  /** 添加专家消息（用于流式输出开始） */
  addStreamingMessage: (expertRole?: ExpertRole) => void;
  /** 更新流式消息内容 */
  updateStreamingMessage: (content: string, append?: boolean) => void;
  /** 结束流式输出 */
  finishStreaming: () => void;
  /** 阶段操作 */
  doPhaseAction: (data: PhaseActionRequest) => Promise<void>;
  /** 切换专家 */
  doSwitchExpert: (data: SwitchExpertRequest) => Promise<void>;
  /** 获取阶段进度 */
  fetchPhaseProgress: (sessionId: number) => Promise<void>;
  /** 获取专家列表 */
  fetchExperts: () => Promise<void>;
  /** 设置当前专家角色 */
  setCurrentExpertRole: (role: ExpertRole) => void;
  /** 清除错误 */
  clearError: () => void;
  /** 重置状态 */
  reset: () => void;
}

export type TechExpertsStore = TechExpertsState & TechExpertsActions;

// ==================== 初始状态 ====================

const initialState: TechExpertsState = {
  sessions: [],
  currentSession: null,
  messages: [],
  experts: [],
  phaseProgress: [],
  currentExpertRole: 'architect',
  loading: {
    sessions: false,
    messages: false,
    send: false,
    phaseAction: false,
    stream: false,
  },
  error: null,
  streamingMessageIndex: null,
  pagination: {
    sessions: { page: 1, pageSize: 20, total: 0 },
    messages: { page: 1, pageSize: 50, total: 0 },
  },
};

// ==================== 工具函数 ====================

/**
 * 根据阶段获取对应专家角色
 */
function getExpertRoleForPhase(phase: ExpertPhase): ExpertRole {
  const roleMap: Record<ExpertPhase, ExpertRole> = {
    architecture: 'architect',
    implementation: 'developer',
    review: 'reviewer',
    testing: 'tester',
  };
  return roleMap[phase];
}

/**
 * 根据专家角色获取专家名称
 */
function getExpertName(role: ExpertRole): string {
  const nameMap: Record<ExpertRole, string> = {
    architect: '架构师',
    developer: '开发工程师',
    reviewer: '代码审查员',
    tester: '测试工程师',
  };
  return nameMap[role];
}

/**
 * 生成临时消息 ID
 */
function generateTempId(): number {
  return Date.now() + Math.random();
}

// ==================== Store 定义 ====================

export const useTechExpertsStore = create<TechExpertsStore>((set, get) => ({
  ...initialState,

  // 获取会话列表
  fetchSessions: async (page = 1, pageSize = 20) => {
    set((state) => ({ loading: { ...state.loading, sessions: true }, error: null }));

    try {
      const response = await getSessions({ page, page_size: pageSize });
      set((state) => ({
        sessions: response.items,
        loading: { ...state.loading, sessions: false },
        pagination: {
          ...state.pagination,
          sessions: {
            page: response.page,
            pageSize: response.page_size,
            total: response.total,
          },
        },
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取会话列表失败';
      set((state) => ({ loading: { ...state.loading, sessions: false }, error: message }));
    }
  },

  // 获取会话详情
  fetchSession: async (sessionId: number) => {
    try {
      const session = await getSession(sessionId);
      set({
        currentSession: session,
        currentExpertRole: getExpertRoleForPhase(session.current_phase),
      });
    } catch (error) {
      console.error('获取会话详情失败:', error);
    }
  },

  // 创建会话
  createSessionItem: async (data: CreateSessionRequest) => {
    const session = await createSession(data);
    set((state) => ({
      sessions: [session, ...state.sessions],
      currentSession: session,
      currentExpertRole: getExpertRoleForPhase(session.current_phase),
      messages: [],
      phaseProgress: [],
    }));
    return session;
  },

  // 删除会话
  deleteSessionItem: async (sessionId: number) => {
    await deleteSession(sessionId);
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== sessionId),
      currentSession: state.currentSession?.id === sessionId ? null : state.currentSession,
    }));
  },

  // 设置当前会话
  setCurrentSession: (session: ExpertSession | null) => {
    set({
      currentSession: session,
      messages: [],
      phaseProgress: [],
      streamingMessageIndex: null,
      currentExpertRole: session ? getExpertRoleForPhase(session.current_phase) : 'architect',
    });
  },

  // 获取消息列表
  fetchMessages: async (sessionId: number, page = 1, pageSize = 50) => {
    set((state) => ({ loading: { ...state.loading, messages: true }, error: null }));

    try {
      const response = await getMessages(sessionId, { page, page_size: pageSize });
      set((state) => ({
        messages: response.items.reverse(), // 旧消息在前
        loading: { ...state.loading, messages: false },
        pagination: {
          ...state.pagination,
          messages: {
            page: response.page,
            pageSize: response.page_size,
            total: response.total,
          },
        },
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取消息列表失败';
      set((state) => ({ loading: { ...state.loading, messages: false }, error: message }));
    }
  },

  // 发送消息
  send: async (data: SendMessageRequest) => {
    set((state) => ({ loading: { ...state.loading, send: true } }));

    try {
      const message = await sendMessage(data);
      set((state) => ({
        messages: [...state.messages, message],
        loading: { ...state.loading, send: false },
      }));
      return message;
    } catch (error) {
      set((state) => ({ loading: { ...state.loading, send: false } }));
      throw error;
    }
  },

  // 添加用户消息（乐观更新）
  addUserMessage: (content: string) => {
    const { currentSession, currentExpertRole } = get();
    if (!currentSession) return;

    const userMessage: ExpertMessage = {
      id: generateTempId(),
      session_id: currentSession.id,
      role: 'user',
      content,
      phase: currentSession.current_phase,
      iteration: currentSession.current_iteration,
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
    }));
  },

  // 添加专家消息（流式输出开始）
  addStreamingMessage: (expertRole?: ExpertRole) => {
    const { currentSession, currentExpertRole } = get();
    if (!currentSession) return;

    const role = expertRole || currentExpertRole;
    const streamingMessage: ExpertMessage = {
      id: generateTempId(),
      session_id: currentSession.id,
      role: 'assistant',
      content: '',
      expert_role: role,
      expert_name: getExpertName(role),
      phase: currentSession.current_phase,
      iteration: currentSession.current_iteration,
      is_streaming: true,
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, streamingMessage],
      streamingMessageIndex: state.messages.length,
      loading: { ...state.loading, stream: true },
    }));
  },

  // 更新流式消息内容
  updateStreamingMessage: (content: string, append = true) => {
    const { streamingMessageIndex, messages } = get();
    if (streamingMessageIndex === null || !messages[streamingMessageIndex]) return;

    const updatedMessages = [...messages];
    const currentMessage = updatedMessages[streamingMessageIndex];
    updatedMessages[streamingMessageIndex] = {
      ...currentMessage,
      content: append ? currentMessage.content + content : content,
    };

    set({ messages: updatedMessages });
  },

  // 结束流式输出
  finishStreaming: () => {
    const { streamingMessageIndex, messages } = get();
    if (streamingMessageIndex === null || !messages[streamingMessageIndex]) return;

    const updatedMessages = [...messages];
    updatedMessages[streamingMessageIndex] = {
      ...updatedMessages[streamingMessageIndex],
      is_streaming: false,
    };

    set({
      messages: updatedMessages,
      streamingMessageIndex: null,
      loading: (state) => ({ ...state, stream: false }),
    });
  },

  // 阶段操作
  doPhaseAction: async (data: PhaseActionRequest) => {
    set((state) => ({ loading: { ...state.loading, phaseAction: true } }));

    try {
      await phaseAction(data);
      // 重新获取会话详情以更新阶段
      await get().fetchSession(data.session_id);
      await get().fetchPhaseProgress(data.session_id);
      set((state) => ({ loading: { ...state.loading, phaseAction: false } }));
    } catch (error) {
      set((state) => ({ loading: { ...state.loading, phaseAction: false } }));
      throw error;
    }
  },

  // 切换专家
  doSwitchExpert: async (data: SwitchExpertRequest) => {
    try {
      const session = await switchExpert(data);
      set({
        currentSession: session,
        currentExpertRole: data.expert_role,
      });
    } catch (error) {
      throw error;
    }
  },

  // 获取阶段进度
  fetchPhaseProgress: async (sessionId: number) => {
    try {
      const progress = await getPhaseProgress(sessionId);
      set({ phaseProgress: progress });
    } catch (error) {
      console.error('获取阶段进度失败:', error);
    }
  },

  // 获取专家列表
  fetchExperts: async () => {
    try {
      const experts = await getExperts();
      set({ experts });
    } catch (error) {
      console.error('获取专家列表失败:', error);
    }
  },

  // 设置当前专家角色
  setCurrentExpertRole: (role: ExpertRole) => {
    set({ currentExpertRole: role });
  },

  // 清除错误
  clearError: () => {
    set({ error: null });
  },

  // 重置状态
  reset: () => {
    set(initialState);
  },
}));
