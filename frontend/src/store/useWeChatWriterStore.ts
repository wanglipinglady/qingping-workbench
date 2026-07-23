/**
 * 微信公众号写作助手状态管理
 */

import { create } from 'zustand';
import {
  getWriterSessions,
  getWriterSession,
  createWriterSession,
  deleteWriterSession,
  startWriting,
  confirmState,
  regenerateOutput,
  rollbackToState,
  getOutputs,
  type CreateWriterSessionRequest,
} from '@/api/wechatWriter';
import type { WriterSession, WriterOutput, WriterState } from '@/api/types';

// ==================== 状态配置 ====================

/** 写作阶段配置 */
export const WRITER_PHASES: { key: WriterState; label: string; icon: string }[] = [
  { key: 'idle', label: '初始化', icon: '🚀' },
  { key: 'topic_confirm', label: '选题确认', icon: '🎯' },
  { key: 'research', label: '资料搜集', icon: '🔍' },
  { key: 'outline', label: '大纲设计', icon: '📐' },
  { key: 'draft', label: '初稿写作', icon: '✍️' },
  { key: 'polish', label: '润色优化', icon: '✨' },
  { key: 'done', label: '已完成', icon: '✅' },
];

/** 专家角色配置 */
export const WRITER_EXPERTS: { key: string; name: string; color: string; avatar: string }[] = [
  { key: 'topic_editor', name: '选题编辑', color: 'bg-emerald-500', avatar: '🎯' },
  { key: 'researcher', name: '研究员', color: 'bg-blue-500', avatar: '🔍' },
  { key: 'outliner', name: '结构师', color: 'bg-orange-500', avatar: '📐' },
  { key: 'writer', name: '撰稿人', color: 'bg-purple-500', avatar: '✍️' },
];

/** 根据状态获取专家 */
export function getExpertForState(state: WriterState): string {
  const map: Record<WriterState, string> = {
    idle: 'topic_editor',
    topic_confirm: 'topic_editor',
    research: 'researcher',
    outline: 'outliner',
    draft: 'writer',
    polish: 'writer',
    done: 'writer',
  };
  return map[state];
}

/** 获取阶段进度 */
export function getPhaseProgress(currentState: WriterState): { phase: WriterState; status: 'completed' | 'current' | 'pending'; label: string }[] {
  const stateOrder: WriterState[] = ['idle', 'topic_confirm', 'research', 'outline', 'draft', 'polish', 'done'];
  const currentIdx = stateOrder.indexOf(currentState);

  return stateOrder.map((state, idx) => {
    const label = WRITER_PHASES.find(p => p.key === state)?.label || state;
    let status: 'completed' | 'current' | 'pending';
    if (idx < currentIdx) status = 'completed';
    else if (idx === currentIdx) status = 'current';
    else status = 'pending';
    return { phase: state, status, label };
  });
}

// ==================== Store 定义 ====================

interface WeChatWriterState {
  sessions: WriterSession[];
  currentSession: WriterSession | null;
  outputs: WriterOutput[];
  loading: {
    sessions: boolean;
    session: boolean;
    start: boolean;
    confirm: boolean;
    regenerate: boolean;
    rollback: boolean;
  };
  error: string | null;
  pagination: { page: number; pageSize: number; total: number };
}

interface WeChatWriterActions {
  fetchSessions: (page?: number, pageSize?: number, status?: string, keyword?: string) => Promise<void>;
  fetchSession: (sessionId: number) => Promise<void>;
  createSessionItem: (data: CreateWriterSessionRequest) => Promise<WriterSession>;
  deleteSessionItem: (sessionId: number) => Promise<void>;
  setCurrentSession: (session: WriterSession | null) => void;
  doStartWriting: (sessionId: number) => Promise<void>;
  doConfirm: (sessionId: number) => Promise<void>;
  doRegenerate: (sessionId: number, feedback?: string) => Promise<void>;
  doRollback: (sessionId: number, targetState: string, reason?: string) => Promise<void>;
  fetchOutputs: (sessionId: number, step?: string) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

const initialState: WeChatWriterState = {
  sessions: [],
  currentSession: null,
  outputs: [],
  loading: {
    sessions: false,
    session: false,
    start: false,
    confirm: false,
    regenerate: false,
    rollback: false,
  },
  error: null,
  pagination: { page: 1, pageSize: 20, total: 0 },
};

export const useWeChatWriterStore = create<WeChatWriterState & WeChatWriterActions>((set, get) => ({
  ...initialState,

  fetchSessions: async (page = 1, pageSize = 20, status, keyword) => {
    set((state) => ({ loading: { ...state.loading, sessions: true }, error: null }));
    try {
      const response = await getWriterSessions({ page, page_size: pageSize, status, keyword });
      set((state) => ({
        sessions: response.items,
        loading: { ...state.loading, sessions: false },
        pagination: { page: response.page, pageSize: response.page_size, total: response.total },
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取会话列表失败';
      set((state) => ({ loading: { ...state.loading, sessions: false }, error: message }));
    }
  },

  fetchSession: async (sessionId: number) => {
    set((state) => ({ loading: { ...state.loading, session: true } }));
    try {
      const session = await getWriterSession(sessionId);
      set({ currentSession: session, loading: { ...get().loading, session: false } });
    } catch (error) {
      set({ loading: { ...get().loading, session: false } });
      console.error('获取会话详情失败:', error);
    }
  },

  createSessionItem: async (data: CreateWriterSessionRequest) => {
    const session = await createWriterSession(data);
    set((state) => ({
      sessions: [session, ...state.sessions],
      currentSession: session,
      outputs: [],
    }));
    return session;
  },

  deleteSessionItem: async (sessionId: number) => {
    await deleteWriterSession(sessionId);
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== sessionId),
      currentSession: state.currentSession?.id === sessionId ? null : state.currentSession,
    }));
  },

  setCurrentSession: (session: WriterSession | null) => {
    set({ currentSession: session, outputs: [] });
  },

  doStartWriting: async (sessionId: number) => {
    set((state) => ({ loading: { ...state.loading, start: true }, error: null }));
    try {
      const result = await startWriting(sessionId);
      // 更新会话状态
      await get().fetchSession(sessionId);
      await get().fetchOutputs(sessionId);
      set((state) => ({ loading: { ...state.loading, start: false } }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '开始写作失败';
      set((state) => ({ loading: { ...state.loading, start: false }, error: message }));
      throw error;
    }
  },

  doConfirm: async (sessionId: number) => {
    set((state) => ({ loading: { ...state.loading, confirm: true } }));
    try {
      await confirmState(sessionId);
      await get().fetchSession(sessionId);
      await get().fetchOutputs(sessionId);
      set((state) => ({ loading: { ...state.loading, confirm: false } }));
    } catch (error) {
      set((state) => ({ loading: { ...state.loading, confirm: false } }));
      throw error;
    }
  },

  doRegenerate: async (sessionId: number, feedback?: string) => {
    set((state) => ({ loading: { ...state.loading, regenerate: true } }));
    try {
      await regenerateOutput(sessionId, feedback);
      await get().fetchSession(sessionId);
      await get().fetchOutputs(sessionId);
      set((state) => ({ loading: { ...state.loading, regenerate: false } }));
    } catch (error) {
      set((state) => ({ loading: { ...state.loading, regenerate: false } }));
      throw error;
    }
  },

  doRollback: async (sessionId: number, targetState: string, reason?: string) => {
    set((state) => ({ loading: { ...state.loading, rollback: true } }));
    try {
      await rollbackToState(sessionId, targetState, reason);
      await get().fetchSession(sessionId);
      set((state) => ({ loading: { ...state.loading, rollback: false } }));
    } catch (error) {
      set((state) => ({ loading: { ...state.loading, rollback: false } }));
      throw error;
    }
  },

  fetchOutputs: async (sessionId: number, step?: string) => {
    try {
      const outputs = await getOutputs(sessionId, step ? { step } : undefined);
      set({ outputs });
    } catch (error) {
      console.error('获取输出版本失败:', error);
    }
  },

  clearError: () => set({ error: null }),
  reset: () => set(initialState),
}));
