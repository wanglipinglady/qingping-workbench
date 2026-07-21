/**
 * 知识库状态管理
 * 管理知识库列表、当前知识库、文档列表、搜索结果等
 */

import { create } from 'zustand';
import {
  getKnowledgeBases,
  getKnowledgeBase,
  createKnowledgeBase,
  updateKnowledgeBase,
  deleteKnowledgeBase,
  getDocuments,
  uploadDocument,
  deleteDocument,
  searchKnowledge,
  getDashboardStats,
  getRecentVisits,
} from '@/api/knowledge';
import type {
  KnowledgeBase,
  Document,
  SearchResult,
  CreateKnowledgeBaseRequest,
  UpdateKnowledgeBaseRequest,
  SearchRequest,
  DashboardStats,
  RecentVisit,
} from '@/api/types';

// ==================== 状态类型定义 ====================

interface KnowledgeState {
  /** 知识库列表 */
  knowledgeBases: KnowledgeBase[];
  /** 当前选中的知识库 */
  currentKnowledgeBase: KnowledgeBase | null;
  /** 文档列表 */
  documents: Document[];
  /** 搜索结果 */
  searchResults: SearchResult[];
  /** 首页统计数据 */
  stats: DashboardStats | null;
  /** 最近访问列表 */
  recentVisits: RecentVisit[];
  /** 加载状态 */
  loading: {
    knowledgeBases: boolean;
    documents: boolean;
    search: boolean;
    stats: boolean;
    upload: boolean;
  };
  /** 错误信息 */
  error: string | null;
  /** 分页信息 */
  pagination: {
    knowledgeBases: { page: number; pageSize: number; total: number };
    documents: { page: number; pageSize: number; total: number };
  };
}

interface KnowledgeActions {
  /** 获取知识库列表 */
  fetchKnowledgeBases: (page?: number, pageSize?: number) => Promise<void>;
  /** 获取知识库详情 */
  fetchKnowledgeBase: (id: number) => Promise<void>;
  /** 创建知识库 */
  createBase: (data: CreateKnowledgeBaseRequest) => Promise<KnowledgeBase>;
  /** 更新知识库 */
  updateBase: (id: number, data: UpdateKnowledgeBaseRequest) => Promise<KnowledgeBase>;
  /** 删除知识库 */
  deleteBase: (id: number) => Promise<void>;
  /** 切换当前知识库 */
  setCurrentKnowledgeBase: (kb: KnowledgeBase | null) => void;
  /** 获取文档列表 */
  fetchDocuments: (knowledgeBaseId: number, page?: number, pageSize?: number) => Promise<void>;
  /** 上传文档 */
  uploadDoc: (
    knowledgeBaseId: number,
    file: File,
    onProgress?: (progress: number) => void
  ) => Promise<Document>;
  /** 删除文档 */
  deleteDoc: (documentId: number) => Promise<void>;
  /** 搜索知识库 */
  search: (data: SearchRequest) => Promise<SearchResult[]>;
  /** 清除搜索结果 */
  clearSearchResults: () => void;
  /** 获取首页统计 */
  fetchStats: () => Promise<void>;
  /** 获取最近访问 */
  fetchRecentVisits: () => Promise<void>;
  /** 清除错误 */
  clearError: () => void;
  /** 重置状态 */
  reset: () => void;
}

export type KnowledgeStore = KnowledgeState & KnowledgeActions;

// ==================== 初始状态 ====================

const initialState: KnowledgeState = {
  knowledgeBases: [],
  currentKnowledgeBase: null,
  documents: [],
  searchResults: [],
  stats: null,
  recentVisits: [],
  loading: {
    knowledgeBases: false,
    documents: false,
    search: false,
    stats: false,
    upload: false,
  },
  error: null,
  pagination: {
    knowledgeBases: { page: 1, pageSize: 20, total: 0 },
    documents: { page: 1, pageSize: 20, total: 0 },
  },
};

// ==================== Store 定义 ====================

export const useKnowledgeStore = create<KnowledgeStore>((set, get) => ({
  ...initialState,

  // 获取知识库列表
  fetchKnowledgeBases: async (page = 1, pageSize = 20) => {
    set((state) => ({ loading: { ...state.loading, knowledgeBases: true }, error: null }));

    try {
      const response = await getKnowledgeBases({ page, page_size: pageSize });
      set((state) => ({
        knowledgeBases: response.items,
        loading: { ...state.loading, knowledgeBases: false },
        pagination: {
          ...state.pagination,
          knowledgeBases: {
            page: response.page,
            pageSize: response.page_size,
            total: response.total,
          },
        },
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取知识库列表失败';
      set((state) => ({ loading: { ...state.loading, knowledgeBases: false }, error: message }));
    }
  },

  // 获取知识库详情
  fetchKnowledgeBase: async (id: number) => {
    try {
      const kb = await getKnowledgeBase(id);
      set({ currentKnowledgeBase: kb });
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取知识库详情失败';
      set({ error: message });
    }
  },

  // 创建知识库
  createBase: async (data: CreateKnowledgeBaseRequest) => {
    const kb = await createKnowledgeBase(data);
    set((state) => ({
      knowledgeBases: [kb, ...state.knowledgeBases],
    }));
    return kb;
  },

  // 更新知识库
  updateBase: async (id: number, data: UpdateKnowledgeBaseRequest) => {
    const kb = await updateKnowledgeBase(id, data);
    set((state) => ({
      knowledgeBases: state.knowledgeBases.map((item) =>
        item.id === id ? kb : item
      ),
      currentKnowledgeBase:
        state.currentKnowledgeBase?.id === id ? kb : state.currentKnowledgeBase,
    }));
    return kb;
  },

  // 删除知识库
  deleteBase: async (id: number) => {
    await deleteKnowledgeBase(id);
    set((state) => ({
      knowledgeBases: state.knowledgeBases.filter((item) => item.id !== id),
      currentKnowledgeBase:
        state.currentKnowledgeBase?.id === id ? null : state.currentKnowledgeBase,
    }));
  },

  // 切换当前知识库
  setCurrentKnowledgeBase: (kb: KnowledgeBase | null) => {
    set({ currentKnowledgeBase: kb });
  },

  // 获取文档列表
  fetchDocuments: async (knowledgeBaseId: number, page = 1, pageSize = 20) => {
    set((state) => ({ loading: { ...state.loading, documents: true }, error: null }));

    try {
      const response = await getDocuments(knowledgeBaseId, { page, page_size: pageSize });
      set((state) => ({
        documents: response.items,
        loading: { ...state.loading, documents: false },
        pagination: {
          ...state.pagination,
          documents: {
            page: response.page,
            pageSize: response.page_size,
            total: response.total,
          },
        },
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取文档列表失败';
      set((state) => ({ loading: { ...state.loading, documents: false }, error: message }));
    }
  },

  // 上传文档
  uploadDoc: async (
    knowledgeBaseId: number,
    file: File,
    onProgress?: (progress: number) => void
  ) => {
    set((state) => ({ loading: { ...state.loading, upload: true } }));

    try {
      const doc = await uploadDocument(knowledgeBaseId, file, onProgress);
      set((state) => ({
        documents: [doc, ...state.documents],
        loading: { ...state.loading, upload: false },
      }));
      return doc;
    } catch (error) {
      set((state) => ({ loading: { ...state.loading, upload: false } }));
      throw error;
    }
  },

  // 删除文档
  deleteDoc: async (documentId: number) => {
    await deleteDocument(documentId);
    set((state) => ({
      documents: state.documents.filter((doc) => doc.id !== documentId),
    }));
  },

  // 搜索知识库
  search: async (data: SearchRequest) => {
    set((state) => ({ loading: { ...state.loading, search: true }, error: null }));

    try {
      const results = await searchKnowledge(data);
      set((state) => ({
        searchResults: results,
        loading: { ...state.loading, search: false },
      }));
      return results;
    } catch (error) {
      const message = error instanceof Error ? error.message : '搜索失败';
      set((state) => ({ loading: { ...state.loading, search: false }, error: message }));
      return [];
    }
  },

  // 清除搜索结果
  clearSearchResults: () => {
    set({ searchResults: [] });
  },

  // 获取首页统计
  fetchStats: async () => {
    set((state) => ({ loading: { ...state.loading, stats: true } }));

    try {
      const stats = await getDashboardStats();
      set((state) => ({
        stats,
        loading: { ...state.loading, stats: false },
      }));
    } catch (error) {
      set((state) => ({ loading: { ...state.loading, stats: false } }));
    }
  },

  // 获取最近访问
  fetchRecentVisits: async () => {
    try {
      const visits = await getRecentVisits();
      set({ recentVisits: visits });
    } catch (error) {
      console.warn('获取最近访问失败:', error);
    }
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
