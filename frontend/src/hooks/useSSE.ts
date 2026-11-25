/**
 * SSE 流式请求 Hook
 * 使用 fetch POST + ReadableStream 处理 Server-Sent Events 流式响应
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { storage } from '@/utils/storage';

// ==================== 类型定义 ====================

export interface SSEOptions {
  /** 连接成功回调 */
  onOpen?: () => void;
  /** 收到消息回调 */
  onMessage?: (data: Record<string, unknown> | string) => void;
  /** 错误回调 */
  onError?: (error: Error) => void;
  /** 连接关闭回调 */
  onClose?: () => void;
  /** 默认请求头 */
  headers?: Record<string, string>;
}

export interface StreamRequestOptions {
  /** POST 请求体（会被 JSON 序列化） */
  body?: unknown;
  /** 额外请求头 */
  headers?: Record<string, string>;
}

export interface UseSSEReturn {
  /** 是否连接中 */
  isConnected: boolean;
  /** 是否正在建立连接 */
  isConnecting: boolean;
  /** 错误信息 */
  error: string | null;
  /** 已接收的消息列表 */
  messages: (Record<string, unknown> | string)[];
  /** 开始连接 */
  startStream: (url: string, options?: StreamRequestOptions) => void;
  /** 停止连接 */
  stopStream: () => void;
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
    headers: defaultHeaders,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<(Record<string, unknown> | string)[]>([]);

  const abortControllerRef = useRef<AbortController | null>(null);

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
    onClose?.();
  }, [onClose]);

  const startStream = useCallback(
    async (url: string, streamOptions: StreamRequestOptions = {}) => {
      stopStream();

      setIsConnecting(true);
      setError(null);
      setMessages([]);

      const controller = new AbortController();
      abortControllerRef.current = controller;

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...defaultHeaders,
        ...streamOptions.headers,
      };
      const token = storage.getToken();
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers,
          body: streamOptions.body !== undefined ? JSON.stringify(streamOptions.body) : undefined,
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`请求失败 (${response.status})`);
        }
        if (!response.body) {
          throw new Error('浏览器不支持流式响应');
        }

        setIsConnected(true);
        setIsConnecting(false);
        onOpen?.();

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          let sepIndex: number;
          while ((sepIndex = buffer.indexOf('\n\n')) !== -1) {
            const rawEvent = buffer.slice(0, sepIndex);
            buffer = buffer.slice(sepIndex + 2);

            const dataLines = rawEvent
              .split('\n')
              .filter((line) => line.startsWith('data:'))
              .map((line) => line.slice(5).trimStart());

            if (dataLines.length === 0) continue;

            const dataStr = dataLines.join('\n');
            let parsed: Record<string, unknown> | string;
            try {
              parsed = JSON.parse(dataStr);
            } catch {
              parsed = dataStr;
            }

            setMessages((prev) => [...prev, parsed]);
            onMessage?.(parsed);
          }
        }
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          // 主动停止，不算错误
        } else {
          const message = err instanceof Error ? err.message : '流式请求失败';
          setError(message);
          onError?.(err instanceof Error ? err : new Error(message));
        }
      } finally {
        setIsConnected(false);
        setIsConnecting(false);
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    },
    [stopStream, defaultHeaders, onOpen, onMessage, onError]
  );

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
    clearMessages,
  };
}

export default useSSE;
