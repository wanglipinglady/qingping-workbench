/**
 * 技术专家组状态管理
 * 管理会话列表、当前会话、消息列表、状态信息等
 */

import { create } from 'zustand';
import {
  getSessions,
  getSession,
  createSession,
  deleteSession,
  getMessages,
  sendMessage,
  confirmState,
  rollbackState,
  switchExpert,
  getStateInfo,
  getExperts,
} from '@/api/techExperts';
import type {
  ExpertSession,
  ExpertMessage,
  Expert,
  CreateSessionRequest,
  SendMessageRequest,
  SwitchExpertRequest,
  RollbackRequest,
  StateInfo,
  ExpertType,
  TechExpertState,
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
  /** 当前状态信息 */
  stateInfo: StateInfo | null;
  /** 当前专家类型 */
  currentExpertRole: ExpertType;
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
  fetchMessages: (sessionId: number) => Promise<void>;
  /** 发送消息（同步模式） */
  send: (data: SendMessageRequest) => Promise<void>;
  /** 添加用户消息（乐观更新） */
  addUserMessage: (content: string) => void;
  /** 添加专家消息（用于流式输出开始） */
  addStreamingMessage: (expertType?: ExpertType) => void;
  /** 更新流式消息内容 */
  updateStreamingMessage: (content: string, append?: boolean) => void;
  /** 结束流式输出 */
  finishStreaming: () => void;
  /** 确认当前状态 */
  doConfirmState: (sessionId: number) => Promise<void>;
  /** 回退到指定状态 */
  doRollbackState: (data: RollbackRequest) => Promise<void>;
  /** 切换专家 */
  doSwitchExpert: (data: SwitchExpertRequest) => Promise<void>;
  /** 获取当前状态信息 */
  fetchStateInfo: (sessionId: number) => Promise<void>;
  /** 获取专家列表 */
  fetchExperts: () => Promise<void>;
  /** 设置当前专家类型 */
  setCurrentExpertRole: (role: ExpertType) => void;
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
  stateInfo: null,
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
  },
};

// ==================== 工具函数 ====================

/**
 * 根据状态获取对应专家类型
 */
function getExpertTypeForState(state: TechExpertState): ExpertType | null {
  const typeMap: Partial<Record<TechExpertState, ExpertType>> = {
    arch_design: 'architect',
    code_impl: 'coder',
    code_review: 'reviewer',
    testing: 'tester',
  };
  return typeMap[state] ?? null;
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
            page,
            pageSize,
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
        currentExpertRole: getExpertTypeForState(session.current_state) ?? 'architect',
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
      currentExpertRole: getExpertTypeForState(session.current_state) ?? 'architect',
      messages: [],
      stateInfo: null,
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
      stateInfo: null,
      streamingMessageIndex: null,
      currentExpertRole: session ? (getExpertTypeForState(session.current_state) ?? 'architect') : 'architect',
    });
  },

  // 获取消息列表
  fetchMessages: async (sessionId: number) => {
    set((state) => ({ loading: { ...state.loading, messages: true }, error: null }));

    try {
      const messages = await getMessages(sessionId);
      set((state) => ({
        messages,
        loading: { ...state.loading, messages: false },
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取消息列表失败';
      set((state) => ({ loading: { ...state.loading, messages: false }, error: message }));
    }
  },

  // 发送消息（同步模式）
  send: async (data: SendMessageRequest) => {
    set((state) => ({ loading: { ...state.loading, send: true } }));

    try {
      await sendMessage(data);
      await get().fetchMessages(data.session_id);
      set((state) => ({ loading: { ...state.loading, send: false } }));
    } catch (error) {
      set((state) => ({ loading: { ...state.loading, send: false } }));
      throw error;
    }
  },

  // 添加用户消息（乐观更新）
  addUserMessage: (content: string) => {
    const { currentSession } = get();
    if (!currentSession) return;

    const userMessage: ExpertMessage = {
      id: generateTempId(),
      session_id: currentSession.id,
      role: 'user',
      content,
      expert_type: null,
      state_label: currentSession.current_state,
      iteration: currentSession.iteration_count,
      created_at: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
    }));
  },

  // 添加专家消息（流式输出开始）
  addStreamingMessage: (expertType?: ExpertType) => {
    const { currentSession, currentExpertRole } = get();
    if (!currentSession) return;

    const type = expertType || currentExpertRole;
    const streamingMessage: ExpertMessage = {
      id: generateTempId(),
      session_id: currentSession.id,
      role: 'assistant',
      content: '',
      expert_type: type,
      state_label: currentSession.current_state,
      iteration: currentSession.iteration_count,
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

  // 确认当前状态
  doConfirmState: async (sessionId: number) => {
    set((state) => ({ loading: { ...state.loading, phaseAction: true } }));

    try {
      await confirmState(sessionId);
      await get().fetchSession(sessionId);
      await get().fetchStateInfo(sessionId);
      set((state) => ({ loading: { ...state.loading, phaseAction: false } }));
    } catch (error) {
      set((state) => ({ loading: { ...state.loading, phaseAction: false } }));
      throw error;
    }
  },

  // 回退到指定状态
  doRollbackState: async (data: RollbackRequest) => {
    set((state) => ({ loading: { ...state.loading, phaseAction: true } }));

    try {
      await rollbackState(data);
      await get().fetchSession(data.session_id);
      await get().fetchStateInfo(data.session_id);
      set((state) => ({ loading: { ...state.loading, phaseAction: false } }));
    } catch (error) {
      set((state) => ({ loading: { ...state.loading, phaseAction: false } }));
      throw error;
    }
  },

  // 切换专家
  doSwitchExpert: async (data: SwitchExpertRequest) => {
    try {
      await switchExpert(data);
      await get().fetchSession(data.session_id);
      await get().fetchStateInfo(data.session_id);
      set({ currentExpertRole: data.expert_type });
    } catch (error) {
      throw error;
    }
  },

  // 获取当前状态信息
  fetchStateInfo: async (sessionId: number) => {
    try {
      const info = await getStateInfo(sessionId);
      set({ stateInfo: info });
    } catch (error) {
      console.error('获取状态信息失败:', error);
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

  // 设置当前专家类型
  setCurrentExpertRole: (role: ExpertType) => {
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
