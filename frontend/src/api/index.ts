/**
 * Axios 实例配置与拦截器
 * 统一处理请求、响应、错误
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { storage } from '@/utils/storage';

// API 基础地址
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// 创建 Axios 实例
const request: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 从本地存储获取 token
    const token = storage.getToken();

    // 如果有 token，添加到请求头
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    // 请求错误处理
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    // 直接返回响应数据
    // 假设后端返回格式为 { code, message, data }
    const data = response.data;

    // 如果是标准响应格式
    if (data && typeof data === 'object' && 'code' in data) {
      // 请求成功
      if (data.code === 200 || data.code === 0) {
        return data.data;
      }

      // 业务错误
      const error = new Error(data.message || '请求失败') as Error & { code?: number };
      error.code = data.code;
      return Promise.reject(error);
    }

    // 非标准格式，直接返回
    return data;
  },
  (error) => {
    const { response } = error;

    if (response) {
      const { status, data } = response;

      switch (status) {
        case 401:
          // 未授权，清除 token 并跳转到登录页
          storage.clearToken();
          storage.clearUser();
          // 跳转到登录页（避免在拦截器中使用 useNavigate）
          if (window.location.pathname !== '/login') {
            window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
          }
          break;

        case 403:
          // 禁止访问
          console.error('权限不足:', data?.message || '您没有权限访问此资源');
          break;

        case 404:
          // 资源不存在
          console.error('资源不存在:', data?.message || '请求的资源不存在');
          break;

        case 500:
          // 服务器错误
          console.error('服务器错误:', data?.message || '服务器内部错误');
          break;

        default:
          console.error(`请求错误 (${status}):`, data?.message || '未知错误');
      }

      // 构造错误对象
      const err = new Error(
        data?.message || data?.detail || `请求失败 (${status})`
      ) as Error & { status?: number; data?: unknown };
      err.status = status;
      err.data = data;

      return Promise.reject(err);
    }

    // 网络错误
    if (error.message === 'Network Error') {
      const err = new Error('网络连接失败，请检查网络设置') as Error & { status?: number };
      err.status = 0;
      return Promise.reject(err);
    }

    // 超时错误
    if (error.code === 'ECONNABORTED') {
      const err = new Error('请求超时，请稍后重试') as Error & { status?: number };
      err.status = 408;
      return Promise.reject(err);
    }

    return Promise.reject(error);
  }
);

/**
 * GET 请求
 * @param url 请求地址
 * @param params 查询参数
 * @param config 额外配置
 */
export function get<T = unknown>(
  url: string,
  params?: Record<string, unknown>,
  config?: AxiosRequestConfig
): Promise<T> {
  return request.get(url, { params, ...config });
}

/**
 * POST 请求
 * @param url 请求地址
 * @param data 请求体数据
 * @param config 额外配置
 */
export function post<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  return request.post(url, data, config);
}

/**
 * PUT 请求
 * @param url 请求地址
 * @param data 请求体数据
 * @param config 额外配置
 */
export function put<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  return request.put(url, data, config);
}

/**
 * PATCH 请求
 * @param url 请求地址
 * @param data 请求体数据
 * @param config 额外配置
 */
export function patch<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  return request.patch(url, data, config);
}

/**
 * DELETE 请求
 * @param url 请求地址
 * @param config 额外配置
 */
export function del<T = unknown>(
  url: string,
  config?: AxiosRequestConfig
): Promise<T> {
  return request.delete(url, config);
}

/**
 * 上传文件
 * @param url 请求地址
 * @param formData FormData 对象
 * @param onProgress 进度回调
 */
export function upload<T = unknown>(
  url: string,
  formData: FormData,
  onProgress?: (progress: number) => void
): Promise<T> {
  return request.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(progress);
      }
    },
  });
}

export default request;
