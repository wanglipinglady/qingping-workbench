/**
 * 选材剪藏相关 API
 */

import { get, post, del } from './index';
import type {
  ClipRequest,
  Clipping,
  ClippingDetail,
  ClippingListResponse,
} from './types';

/** 剪藏列表查询参数 */
export interface ClippingQuery {
  page?: number;
  page_size?: number;
  keyword?: string;
  category?: string;
}

/**
 * 剪藏网页到知识库
 * @param data 剪藏参数
 */
export function clipWebPage(data: ClipRequest): Promise<ClippingDetail> {
  return post<ClippingDetail>('/clipper/clip', data);
}

/**
 * 获取剪藏列表
 */
export function getClippings(params?: ClippingQuery): Promise<ClippingListResponse> {
  return get<ClippingListResponse>('/clipper/items', params);
}

/**
 * 获取剪藏详情（含正文 Markdown）
 */
export function getClippingDetail(id: number): Promise<ClippingDetail> {
  return get<ClippingDetail>(`/clipper/items/${id}`);
}

/**
 * 删除剪藏（同步删除知识库文档与向量）
 */
export function deleteClipping(id: number): Promise<void> {
  return del<void>(`/clipper/items/${id}`);
}

/**
 * 生成书签小工具代码
 * 点击书签后新开一个工作台剪藏页，URL 自动预填并触发剪藏。
 */
export function buildBookmarklet(): string {
  const origin = window.location.origin;
  return (
    "javascript:(function(){window.open('" +
    origin +
    "/clipper?url='+encodeURIComponent(location.href),'_blank');})();"
  );
}
