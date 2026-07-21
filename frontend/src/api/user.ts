/**
 * 用户相关 API
 * 与后端 /api/users 路由对齐
 */

import { get, post, put } from './index';
import type {
  User,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
} from './types';

/**
 * 用户登录
 * @param data 登录信息
 */
export function login(data: LoginRequest): Promise<LoginResponse> {
  return post<LoginResponse>('/users/login', data);
}

/**
 * 用户注册
 * @param data 注册信息
 */
export function register(data: RegisterRequest): Promise<LoginResponse> {
  return post<LoginResponse>('/users/register', data);
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser(): Promise<User> {
  return get<User>('/users/me');
}

/**
 * 更新当前用户信息
 * @param data 用户信息
 */
export function updateProfile(data: Partial<User>): Promise<User> {
  return put<User>('/users/me', data);
}

/**
 * 登出（前端清除 token 即可，后端无状态 JWT）
 */
export function logout(): void {
  localStorage.removeItem('token');
}
