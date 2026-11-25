/**
 * 系统相关 API
 * 动态插件 / 菜单数据
 */
import { get } from './index';

export interface MenuItem {
  key: string;
  label: string;
  icon: string | null;
  path: string | null;
  order: number;
  children?: MenuItem[];
}

export interface PluginInfo {
  name: string;
  description: string;
  version: string;
}

export interface PluginsResponse {
  plugins: PluginInfo[];
  menus: MenuItem[];
}

/**
 * 获取已加载插件与动态菜单
 * 响应拦截器已解包 unified_response 的 data 字段
 */
export function getPlugins(): Promise<PluginsResponse> {
  return get<PluginsResponse>('/plugins');
}
