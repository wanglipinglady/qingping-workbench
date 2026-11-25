/**
 * 知识库相关 API
 */

import { get, post, put, del, upload } from './index';
import type {
  KnowledgeBase,
  Document,
  CreateKnowledgeBaseRequest,
  UpdateKnowledgeBaseRequest,
  SearchRequest,
  SearchResponse,
  PaginatedResponse,
  PaginationParams,
  DashboardStats,
  RecentVisit,
} from './types';

/**
 * 获取知识库列表
 * @param params 分页参数
 */
export function getKnowledgeBases(
  params?: PaginationParams
): Promise<PaginatedResponse<KnowledgeBase>> {
  return get<PaginatedResponse<KnowledgeBase>>('/knowledge-bases', params);
}

/**
 * 获取知识库详情
 * @param id 知识库 ID
 */
export function getKnowledgeBase(id: number): Promise<KnowledgeBase> {
  return get<KnowledgeBase>(`/knowledge-bases/${id}`);
}

/**
 * 创建知识库
 * @param data 知识库信息
 */
export function createKnowledgeBase(
  data: CreateKnowledgeBaseRequest
): Promise<KnowledgeBase> {
  return post<KnowledgeBase>('/knowledge-bases', data);
}

/**
 * 更新知识库
 * @param id 知识库 ID
 * @param data 更新信息
 */
export function updateKnowledgeBase(
  id: number,
  data: UpdateKnowledgeBaseRequest
): Promise<KnowledgeBase> {
  return put<KnowledgeBase>(`/knowledge-bases/${id}`, data);
}

/**
 * 删除知识库
 * @param id 知识库 ID
 */
export function deleteKnowledgeBase(id: number): Promise<void> {
  return del<void>(`/knowledge-bases/${id}`);
}

/**
 * 获取文档列表
 * @param knowledgeBaseId 知识库 ID
 * @param params 分页参数
 */
export function getDocuments(
  knowledgeBaseId: number,
  params?: PaginationParams
): Promise<PaginatedResponse<Document>> {
  return get<PaginatedResponse<Document>>(
    `/knowledge-bases/${knowledgeBaseId}/documents`,
    params
  );
}


/**
 * 上传文档
 * @param knowledgeBaseId 知识库 ID
 * @param file 文件对象
 * @param onProgress 上传进度回调
 */
export function uploadDocument(
  knowledgeBaseId: number,
  file: File,
  onProgress?: (progress: number) => void
): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);

  return upload<Document>(
    `/knowledge-bases/${knowledgeBaseId}/documents/upload`,
    formData,
    onProgress
  );
}

/**
 * 删除文档
 * @param kbId 知识库 ID
 * @param docId 文档 ID
 */
export function deleteDocument(kbId: number, docId: number): Promise<void> {
  return del<void>(`/knowledge-bases/${kbId}/documents/${docId}`);
}

/**
 * 搜索知识库
 * @param data 搜索参数
 */
export function searchKnowledge(data: SearchRequest): Promise<SearchResponse> {
  const { knowledge_base_id, ...body } = data;
  return post<SearchResponse>(`/knowledge-bases/${knowledge_base_id}/search`, body);
}

/**
 * 获取首页统计数据
 */
export function getDashboardStats(): Promise<DashboardStats> {
  return get<DashboardStats>('/knowledge/stats');
}

/**
 * 获取最近访问列表
 */
export function getRecentVisits(): Promise<RecentVisit[]> {
  return get<RecentVisit[]>('/knowledge/recent-visits');
}
