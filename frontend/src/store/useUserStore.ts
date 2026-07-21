/**
 * 用户状态管理
 * 存储用户信息、token、登录状态等
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { storage } from '@/utils/storage';
import { login as loginApi, getCurrentUser } from '@/api/user';
import type { User, LoginRequest, LoginResponse } from '@/api/types';

// ==================== 状态类型定义 ====================

interface UserState {
  /** 用户信息 */
  user: User | null;
  /** 访问令牌 */
  token: string | null;
  /** 是否正在加载 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 是否记住密码 */
  rememberMe: boolean;
  /** 保存的登录名（记住密码时使用） */
  savedUsername: string;
}

interface UserActions {
  /** 登录 */
  login: (data: LoginRequest) => Promise<LoginResponse>;
  /** 登出 */
  logout: () => Promise<void>;
  /** 获取当前用户信息 */
  fetchCurrentUser: () => Promise<User | null>;
  /** 设置用户信息 */
  setUser: (user: User | null) => void;
  /** 设置 token */
  setToken: (token: string | null) => void;
  /** 设置记住密码 */
  setRememberMe: (remember: boolean, username?: string) => void;
  /** 清除错误 */
  clearError: () => void;
  /** 重置状态 */
  reset: () => void;
}

export type UserStore = UserState & UserActions;

// ==================== 初始状态 ====================

const initialState: UserState = {
  user: null,
  token: null,
  loading: false,
  error: null,
  rememberMe: false,
  savedUsername: '',
};

// ==================== Store 定义 ====================

export const useUserStore = create<UserStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      // 登录
      login: async (data: LoginRequest) => {
        set({ loading: true, error: null });

        try {
          const response = await loginApi(data);

          // 保存 token 和用户信息
          set({
            token: response.access_token,
            user: response.user,
            loading: false,
            error: null,
          });

          // 同步到本地存储
          storage.setToken(response.access_token);
          storage.setUser(response.user);

          // 如果记住密码，保存用户名
          if (get().rememberMe) {
            storage.setRememberedUsername(data.username);
          } else {
            storage.clearRememberedUsername();
          }

          return response;
        } catch (error) {
          const message = error instanceof Error ? error.message : '登录失败';
          set({ loading: false, error: message });
          throw error;
        }
      },

      // 登出（后端无状态 JWT，前端清除 token 即可）
      logout: () => {
        // 清除本地存储
        storage.clearToken();
        storage.clearUser();

        // 重置状态（保留记住密码设置）
        const { rememberMe, savedUsername } = get();
        set({
          ...initialState,
          rememberMe,
          savedUsername,
        });
      },

      // 获取当前用户信息
      fetchCurrentUser: async () => {
        set({ loading: true, error: null });

        try {
          const user = await getCurrentUser();
          set({ user, loading: false, error: null });
          storage.setUser(user);
          return user;
        } catch (error) {
          const message = error instanceof Error ? error.message : '获取用户信息失败';
          set({ loading: false, error: message });
          return null;
        }
      },

      // 设置用户信息
      setUser: (user: User | null) => {
        set({ user });
        if (user) {
          storage.setUser(user);
        } else {
          storage.clearUser();
        }
      },

      // 设置 token
      setToken: (token: string | null) => {
        set({ token });
        if (token) {
          storage.setToken(token);
        } else {
          storage.clearToken();
        }
      },

      // 设置记住密码
      setRememberMe: (remember: boolean, username?: string) => {
        set({
          rememberMe: remember,
          savedUsername: username || get().savedUsername,
        });
        if (remember && username) {
          storage.setRememberedUsername(username);
        } else if (!remember) {
          storage.clearRememberedUsername();
        }
      },

      // 清除错误
      clearError: () => {
        set({ error: null });
      },

      // 重置状态
      reset: () => {
        storage.clearToken();
        storage.clearUser();
        set(initialState);
      },
    }),
    {
      name: 'user-storage',
      // 只持久化部分状态
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        rememberMe: state.rememberMe,
        savedUsername: state.savedUsername,
      }),
    }
  )
);
