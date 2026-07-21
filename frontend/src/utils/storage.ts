/**
 * 本地存储工具
 * 封装 localStorage 操作，支持 JSON 序列化
 */

import type { User } from '@/api/types';

// 存储键名常量
const TOKEN_KEY = 'qingping_token';
const USER_KEY = 'qingping_user';
const REMEMBERED_USERNAME_KEY = 'qingping_remembered_username';

/**
 * Token 相关操作
 */
export const tokenStorage = {
  /** 获取 token */
  get(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  /** 设置 token */
  set(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  },

  /** 清除 token */
  clear(): void {
    localStorage.removeItem(TOKEN_KEY);
  },
};

/**
 * 用户信息相关操作
 */
export const userStorage = {
  /** 获取用户信息 */
  get(): User | null {
    const userStr = localStorage.getItem(USER_KEY);
    if (!userStr) return null;
    try {
      return JSON.parse(userStr) as User;
    } catch {
      return null;
    }
  },

  /** 设置用户信息 */
  set(user: User): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  /** 清除用户信息 */
  clear(): void {
    localStorage.removeItem(USER_KEY);
  },
};

/**
 * 记住密码相关
 */
export const rememberStorage = {
  /** 获取记住的用户名 */
  getUsername(): string | null {
    return localStorage.getItem(REMEMBERED_USERNAME_KEY);
  },

  /** 设置记住的用户名 */
  setUsername(username: string): void {
    localStorage.setItem(REMEMBERED_USERNAME_KEY, username);
  },

  /** 清除记住的用户名 */
  clearUsername(): void {
    localStorage.removeItem(REMEMBERED_USERNAME_KEY);
  },
};

/**
 * 统一的存储操作对象（兼容旧代码）
 */
export const storage = {
  // Token
  getToken: tokenStorage.get,
  setToken: tokenStorage.set,
  clearToken: tokenStorage.clear,

  // 用户信息
  getUser: userStorage.get,
  setUser: userStorage.set,
  clearUser: userStorage.clear,

  // 记住密码
  getRememberedUsername: rememberStorage.getUsername,
  setRememberedUsername: rememberStorage.setUsername,
  clearRememberedUsername: rememberStorage.clearUsername,

  /**
   * 清除所有存储的数据
   */
  clearAll(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(REMEMBERED_USERNAME_KEY);
  },

  /**
   * 通用获取
   */
  get<T = unknown>(key: string): T | null {
    const value = localStorage.getItem(key);
    if (!value) return null;
    try {
      return JSON.parse(value) as T;
    } catch {
      return value as unknown as T;
    }
  },

  /**
   * 通用设置
   */
  set<T = unknown>(key: string, value: T): void {
    if (typeof value === 'string') {
      localStorage.setItem(key, value);
    } else {
      localStorage.setItem(key, JSON.stringify(value));
    }
  },

  /**
   * 通用删除
   */
  remove(key: string): void {
    localStorage.removeItem(key);
  },
};

export default storage;
