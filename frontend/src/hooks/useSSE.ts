/**
 * SSE 流式请求 Hook
 * 用于处理 Server-Sent Events 流式响应
 */

import { useState, useRef, useCallback, useEffect } from 'react';

// ==================== 类型定义 ====================

export interface SSEOptions {
  /** 连接成功回调 */
  onOpen?: () => void;
  /** 收到消息回调 */
  onMessage?: (data: Record<string, unknown> | string) => void;
  /** 错误回调 */
  onError?: (error: Event) => void;
  /** 连接关闭回调 */
  onClose?: () => void;
  /** 自定义请求头 */
  headers?: Record<string, string>;
  /** 是否自动重连 */
  autoReconnect?: boolean;
  /** 最大重连次数 */
  maxReconnectAttempts?: number;
  /** 重连间隔（毫秒） */
  reconnectInterval?: number;
}

export interface UseSSEReturn {
  /** 是否连接中 */
  isConnected: boolean;
  /** 是否正在连接 */
  isConnecting: boolean;
  /** 错误信息 */
  error: string | null;
  /** 已接收的消息列表 */
  messages: (Record<string, unknown> | string)[];
  /** 开始连接 */
  startStream: (url: string) => void;
  /** 停止连接 */
  stopStream: () => void;
  /** 重连 */
  reconnect: () => void;
  /** 清空消息 */
  clearMessages: () => void;
}

// ==================== Hook 实现 ====================

export function useSSE(options: SSEOptions = {}): UseSSEReturn {
  const {
    onOpen,
    onMessage,
    onError,
    onClose,
    autoReconnect = false,
    maxReconnectAttempts = 3,
    reconnectInterval = 1000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<(Record<string, unknown> | string)[]>([]);

  const eventSourceRef = useRef<EventSource | null>(null);
  const urlRef = useRef<string>('');
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<number | null>(null);

  /**
   * 处理连接打开
   */
  const handleOpen = useCallback(() => {
    setIsConnected(true);
    setIsConnecting(false);
    setError(null);
    reconnectAttemptsRef.current = 0;
    onOpen?.();
  }, [onOpen]);

  /**
   * 处理消息接收
   */
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      let data: Record<string, unknown> | string;

      try {
        data = JSON.parse(event.data);
      } catch {
        data = event.data;
      }

      setMessages((prev) => [...prev, data]);
      onMessage?.(data);
    },
    [onMessage]
  );

  /**
   * 处理错误
   */
  const handleError = useCallback(
    (event: Event) => {
      setIsConnected(false);
      setIsConnecting(false);
      setError('SSE 连接错误');

      // 自动重连
      if (autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
        reconnectAttemptsRef.current += 1;
        const delay = reconnectInterval * reconnectAttemptsRef.current;

        reconnectTimerRef.current = window.setTimeout(() => {
          if (urlRef.current) {
            startStreamInternal(urlRef.current);
          }
        }, delay);
      }

      onError?.(event);
    },
    [autoReconnect, maxReconnectAttempts, reconnectInterval, onError]
  );

  /**
   * 内部开始连接
   */
  const startStreamInternal = useCallback(
    (url: string) => {
      // 清除旧的连接
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }

      setIsConnecting(true);
      setError(null);

      try {
        const eventSource = new EventSource(url);
        eventSourceRef.current = eventSource;

        eventSource.onopen = handleOpen;
        eventSource.onmessage = handleMessage;
        eventSource.onerror = handleError;
      } catch (err) {
        setIsConnecting(false);
        setError(err instanceof Error ? err.message : '创建 SSE 连接失败');
      }
    },
    [handleOpen, handleMessage, handleError]
  );

  /**
   * 开始流式连接
   */
  const startStream = useCallback(
    (url: string) => {
      urlRef.current = url;
      reconnectAttemptsRef.current = 0;
      setMessages([]);
      startStreamInternal(url);
    },
    [startStreamInternal]
  );

  /**
   * 停止流式连接
   */
  const stopStream = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
    onClose?.();
  }, [onClose]);

  /**
   * 重连
   */
  const reconnect = useCallback(() => {
    if (urlRef.current) {
      reconnectAttemptsRef.current = 0;
      startStreamInternal(urlRef.current);
    }
  }, [startStreamInternal]);

  /**
   * 清空消息
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      stopStream();
    };
  }, [stopStream]);

  return {
    isConnected,
    isConnecting,
    error,
    messages,
    startStream,
    stopStream,
    reconnect,
    clearMessages,
  };
}

export default useSSE;
