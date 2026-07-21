/**
 * 技术专家组页面
 * 左侧会话列表、顶部状态进度条、中间对话区域、底部输入框
 * 支持 SSE 流式输出、阶段切换、专家切换
 */

import { useState, useEffect, useRef } from 'react';
import { useTechExpertsStore } from '@/store/useTechExpertsStore';
import { useKnowledgeStore } from '@/store/useKnowledgeStore';
import Button from '@/components/Common/Button';
import Modal from '@/components/Common/Modal';
import Input from '@/components/Common/Input';
import MarkdownRender from '@/components/MarkdownRender';
import { useSSE } from '@/hooks/useSSE';
import { formatDate } from '@/utils/format';
import type { ExpertPhase, ExpertRole, ExpertMessage } from '@/api/types';

// 阶段配置
const phases: { key: ExpertPhase; label: string; icon: string }[] = [
  { key: 'architecture', label: '架构设计', icon: '🏗️' },
  { key: 'implementation', label: '代码实现', icon: '💻' },
  { key: 'review', label: '代码审查', icon: '🔍' },
  { key: 'testing', label: '测试验证', icon: '🧪' },
];

// 专家角色配置
const expertRoles: { key: ExpertRole; name: string; color: string; borderColor: string; avatar: string }[] = [
  { key: 'architect', name: '架构师', color: 'bg-purple-500', borderColor: 'border-l-purple-500', avatar: '👨‍🎨' },
  { key: 'developer', name: '开发工程师', color: 'bg-primary-500', borderColor: 'border-l-primary-500', avatar: '👨‍💻' },
  { key: 'reviewer', name: '代码审查员', color: 'bg-accent-500', borderColor: 'border-l-accent-500', avatar: '🧐' },
  { key: 'tester', name: '测试工程师', color: 'bg-danger-500', borderColor: 'border-l-danger-500', avatar: '🧪' },
];

export default function TechExperts() {
  const {
    sessions,
    currentSession,
    messages,
    currentExpertRole,
    loading,
    fetchSessions,
    createSessionItem,
    setCurrentSession,
    fetchMessages,
    addUserMessage,
    addStreamingMessage,
    updateStreamingMessage,
    finishStreaming,
    doPhaseAction,
    doSwitchExpert,
    setCurrentExpertRole,
  } = useTechExpertsStore();

  const { knowledgeBases, fetchKnowledgeBases } = useKnowledgeStore();

  const [showNewSessionModal, setShowNewSessionModal] = useState(false);
  const [newSessionTitle, setNewSessionTitle] = useState('');
  const [newSessionKbId, setNewSessionKbId] = useState<number | undefined>();
  const [inputValue, setInputValue] = useState('');
  const [showExpertDropdown, setShowExpertDropdown] = useState(false);
  const [showKbDropdown, setShowKbDropdown] = useState(false);
  const [showInsertCode, setShowInsertCode] = useState(false);
  const [codeContent, setCodeContent] = useState('');
  const [codeLanguage, setCodeLanguage] = useState('python');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const expertDropdownRef = useRef<HTMLDivElement>(null);
  const kbDropdownRef = useRef<HTMLDivElement>(null);

  // SSE Hook
  const { isConnected, startStream, stopStream } = useSSE({
    onMessage: (data) => {
      if (data.content) {
        updateStreamingMessage(data.content, true);
      }
      if (data.done) {
        finishStreaming();
      }
    },
    onError: (error) => {
      console.error('SSE 错误:', error);
      finishStreaming();
    },
  });

  // 初始化
  useEffect(() => {
    fetchSessions();
    fetchKnowledgeBases();
  }, [fetchSessions, fetchKnowledgeBases]);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (expertDropdownRef.current && !expertDropdownRef.current.contains(e.target as Node)) {
        setShowExpertDropdown(false);
      }
      if (kbDropdownRef.current && !kbDropdownRef.current.contains(e.target as Node)) {
        setShowKbDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 自动调整输入框高度
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [inputValue]);

  // 获取阶段状态
  const getPhaseStatus = (phase: ExpertPhase): 'completed' | 'current' | 'pending' => {
    if (!currentSession) return 'pending';
    const currentIndex = phases.findIndex((p) => p.key === currentSession.current_phase);
    const phaseIndex = phases.findIndex((p) => p.key === phase);
    if (phaseIndex < currentIndex) return 'completed';
    if (phaseIndex === currentIndex) return 'current';
    return 'pending';
  };

  // 创建会话
  const handleCreateSession = async () => {
    if (!newSessionTitle.trim()) return;
    try {
      const session = await createSessionItem({
        title: newSessionTitle.trim(),
        knowledge_base_id: newSessionKbId,
      });
      setShowNewSessionModal(false);
      setNewSessionTitle('');
      setNewSessionKbId(undefined);
      await fetchMessages(session.id);
    } catch (error) {
      console.error('创建会话失败:', error);
    }
  };

  // 选择会话
  const handleSelectSession = async (sessionId: number) => {
    const session = sessions.find((s) => s.id === sessionId);
    if (session) {
      setCurrentSession(session);
      await fetchMessages(sessionId);
    }
  };

  // 发送消息
  const handleSend = async () => {
    if (!inputValue.trim() || !currentSession || loading.stream) return;

    const content = inputValue.trim();
    setInputValue('');

    // 添加用户消息
    addUserMessage(content);

    // 开始流式输出
    addStreamingMessage(currentExpertRole);

    // 构建 SSE URL
    const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
    const token = localStorage.getItem('user-storage') 
      ? JSON.parse(localStorage.getItem('user-storage') || '{}').state?.token 
      : '';
    const url = `${baseUrl}/tech-experts/stream?session_id=${currentSession.id}&content=${encodeURIComponent(content)}&expert_role=${currentExpertRole}&token=${token}`;

    startStream(url);
  };

  // 确认进入下一阶段
  const handleConfirmPhase = async () => {
    if (!currentSession) return;
    try {
      await doPhaseAction({
        session_id: currentSession.id,
        action: 'confirm',
      });
      // 切换到对应专家
      const nextPhaseIndex = phases.findIndex((p) => p.key === currentSession.current_phase) + 1;
      if (nextPhaseIndex < phases.length) {
        const nextPhase = phases[nextPhaseIndex].key;
        const roleMap: Record<ExpertPhase, ExpertRole> = {
          architecture: 'architect',
          implementation: 'developer',
          review: 'reviewer',
          testing: 'tester',
        };
        setCurrentExpertRole(roleMap[nextPhase]);
      }
    } catch (error) {
      console.error('阶段确认失败:', error);
    }
  };

  // 回退修改
  const handleRollback = async () => {
    if (!currentSession) return;
    try {
      await doPhaseAction({
        session_id: currentSession.id,
        action: 'rollback',
      });
    } catch (error) {
      console.error('回退失败:', error);
    }
  };

  // 切换专家
  const handleSwitchExpert = async (role: ExpertRole) => {
    if (!currentSession) return;
    try {
      await doSwitchExpert({
        session_id: currentSession.id,
        expert_role: role,
      });
      setShowExpertDropdown(false);
    } catch (error) {
      console.error('切换专家失败:', error);
    }
  };

  // 插入代码
  const handleInsertCode = () => {
    if (!codeContent.trim()) return;
    const codeBlock = `\`\`\`${codeLanguage}\n${codeContent}\n\`\`\`\n`;
    setInputValue((prev) => prev + codeBlock);
    setShowInsertCode(false);
    setCodeContent('');
    textareaRef.current?.focus();
  };

  // 键盘快捷键
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 获取当前专家信息
  const currentExpert = expertRoles.find((e) => e.key === currentExpertRole);

  return (
    <div className="h-full flex">
      {/* 左侧会话列表 */}
      <div className="w-72 bg-white border-r border-gray-100 flex flex-col">
        <div className="p-4 border-b border-gray-50">
          <Button block onClick={() => setShowNewSessionModal(true)}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新建对话
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {loading.sessions ? (
            <div className="py-8 text-center">
              <div className="w-6 h-6 border-2 border-primary-200 border-t-primary-500 rounded-full animate-spin mx-auto" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-8 text-text-tertiary text-sm">
              暂无对话
            </div>
          ) : (
            <div className="space-y-1">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  onClick={() => handleSelectSession(session.id)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    currentSession?.id === session.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'hover:bg-gray-50 text-text-secondary'
                  }`}
                >
                  <div className="font-medium truncate mb-1">{session.title}</div>
                  <div className="flex items-center gap-2 text-xs text-text-tertiary">
                    <span className={`px-1.5 py-0.5 rounded text-xs ${
                      session.current_phase === 'architecture' ? 'bg-purple-100 text-purple-600' :
                      session.current_phase === 'implementation' ? 'bg-primary-100 text-primary-600' :
                      session.current_phase === 'review' ? 'bg-accent-100 text-accent-600' :
                      'bg-danger-100 text-danger-600'
                    }`}>
                      {phases.find((p) => p.key === session.current_phase)?.label}
                    </span>
                    <span>第 {session.current_iteration} 轮</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 右侧主内容区 */}
      <div className="flex-1 flex flex-col min-w-0 bg-bg">
        {currentSession ? (
          <>
            {/* 顶部状态进度条 */}
            <div className="bg-white border-b border-gray-100 px-6 py-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold text-text">{currentSession.title}</h2>
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-text-tertiary">迭代轮次：</span>
                  <span className="font-medium text-primary-600">第 {currentSession.current_iteration} 轮</span>
                </div>
              </div>

              {/* 阶段进度 */}
              <div className="flex items-center justify-between">
                {phases.map((phase, index) => {
                  const status = getPhaseStatus(phase.key);
                  return (
                    <div key={phase.key} className="flex items-center flex-1">
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all ${
                            status === 'completed'
                              ? 'bg-gray-200 text-gray-500'
                              : status === 'current'
                              ? `bg-primary-500 text-white animate-pulse`
                              : 'bg-white border-2 border-gray-200 text-gray-300'
                          }`}
                        >
                          {status === 'completed' ? (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          ) : (
                            <span className="text-xs">{index + 1}</span>
                          )}
                        </div>
                        <span
                          className={`text-sm font-medium ${
                            status === 'completed'
                              ? 'text-gray-400'
                              : status === 'current'
                              ? 'text-primary-600'
                              : 'text-gray-300'
                          }`}
                        >
                          {phase.label}
                        </span>
                      </div>
                      {index < phases.length - 1 && (
                        <div
                          className={`flex-1 h-0.5 mx-3 ${
                            status === 'completed' ? 'bg-gray-200' : 'bg-gray-100'
                          }`}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 对话区域 */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <div className="w-20 h-20 mb-4 bg-white rounded-2xl shadow-soft flex items-center justify-center text-4xl">
                    {currentExpert?.avatar}
                  </div>
                  <h3 className="text-xl font-semibold text-text mb-2">
                    {currentExpert?.name}已就位
                  </h3>
                  <p className="text-text-secondary max-w-md">
                    您好！我是{currentExpert?.name}，很高兴为您服务。请描述您的需求，我将为您提供专业的{phases.find((p) => p.key === currentSession.current_phase)?.label}服务。
                  </p>
                </div>
              ) : (
                messages.map((message: ExpertMessage, index: number) => (
                  <div
                    key={message.id || index}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {message.role === 'assistant' && (
                      <div className="flex gap-3 max-w-3xl">
                        {/* 专家头像 */}
                        <div className="flex-shrink-0">
                          <div className={`w-10 h-10 rounded-full ${expertRoles.find((e) => e.key === message.expert_role)?.color || 'bg-primary-500'} flex items-center justify-center text-white text-lg`}>
                            {expertRoles.find((e) => e.key === message.expert_role)?.avatar || '🤖'}
                          </div>
                        </div>

                        {/* 消息内容 */}
                        <div className={`flex-1 bg-white rounded-xl shadow-soft p-4 border-l-4 ${expertRoles.find((e) => e.key === message.expert_role)?.borderColor || 'border-l-primary-500'}`}>
                          {/* 专家标签 */}
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-medium text-text text-sm">
                              {message.expert_name || '专家'}
                            </span>
                            <span className="px-2 py-0.5 bg-gray-100 text-text-tertiary text-xs rounded">
                              {phases.find((p) => p.key === message.phase)?.label}
                            </span>
                            <span className="text-xs text-text-tertiary">
                              第 {message.iteration} 轮
                            </span>
                          </div>

                          {/* 消息正文 */}
                          <div className="text-text-secondary">
                            {message.content ? (
                              <MarkdownRender content={message.content} />
                            ) : message.is_streaming ? (
                              <div className="flex items-center gap-1 text-text-tertiary">
                                <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                              </div>
                            ) : null}
                          </div>

                          {/* 操作区：只有最后一条专家消息且非流式输出时显示 */}
                          {index === messages.length - 1 && message.role === 'assistant' && !message.is_streaming && (
                            <div className="mt-4 pt-4 border-t border-gray-50 flex items-center gap-2">
                              <Button
                                size="sm"
                                onClick={handleConfirmPhase}
                                disabled={loading.phaseAction}
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                确认进入下一阶段
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={handleRollback}
                                disabled={loading.phaseAction || currentSession.current_iteration <= 1}
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                                </svg>
                                回退修改
                              </Button>

                              {/* 切换专家下拉 */}
                              <div className="relative ml-auto" ref={expertDropdownRef}>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => setShowExpertDropdown(!showExpertDropdown)}
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                                  </svg>
                                  切换专家
                                </Button>
                                {showExpertDropdown && (
                                  <div className="absolute right-0 top-full mt-1 w-40 bg-white rounded-lg shadow-large border border-gray-100 py-1 z-10 animate-fade-in">
                                    {expertRoles.map((expert) => (
                                      <button
                                        key={expert.key}
                                        onClick={() => handleSwitchExpert(expert.key)}
                                        className={`w-full px-3 py-2 text-left text-sm flex items-center gap-2 hover:bg-gray-50 ${
                                          currentExpertRole === expert.key
                                            ? 'text-primary-600 bg-primary-50'
                                            : 'text-text-secondary'
                                        }`}
                                      >
                                        <span>{expert.avatar}</span>
                                        {expert.name}
                                      </button>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {message.role === 'user' && (
                      <div className="max-w-xl">
                        <div className="bg-primary-500 text-white rounded-xl p-4 shadow-soft">
                          <p className="whitespace-pre-wrap break-words">{message.content}</p>
                        </div>
                        <div className="text-xs text-text-tertiary mt-1 text-right">
                          {formatDate(message.created_at, 'HH:mm')}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* 底部输入区 */}
            <div className="bg-white border-t border-gray-100 p-4">
              {/* 工具栏 */}
              <div className="flex items-center gap-2 mb-2">
                <button
                  onClick={() => setShowInsertCode(true)}
                  className="p-2 rounded-lg text-text-tertiary hover:text-text-secondary hover:bg-gray-50 transition-colors"
                  title="插入代码"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                </button>

                <button
                  className="p-2 rounded-lg text-text-tertiary hover:text-text-secondary hover:bg-gray-50 transition-colors"
                  title="上传文件"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                </button>

                {/* 选择知识库 */}
                <div className="relative" ref={kbDropdownRef}>
                  <button
                    onClick={() => setShowKbDropdown(!showKbDropdown)}
                    className="p-2 rounded-lg text-text-tertiary hover:text-text-secondary hover:bg-gray-50 transition-colors flex items-center gap-1"
                    title="选择知识库"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    <span className="text-xs">知识库</span>
                  </button>
                  {showKbDropdown && (
                    <div className="absolute left-0 bottom-full mb-1 w-56 bg-white rounded-lg shadow-large border border-gray-100 py-1 z-10 animate-fade-in max-h-64 overflow-y-auto">
                      <div className="px-3 py-2 text-xs text-text-tertiary border-b border-gray-50">
                        选择关联知识库
                      </div>
                      {knowledgeBases.length === 0 ? (
                        <div className="px-3 py-4 text-center text-sm text-text-tertiary">
                          暂无知识库
                        </div>
                      ) : (
                        knowledgeBases.map((kb) => (
                          <button
                            key={kb.id}
                            onClick={() => {
                              setNewSessionKbId(kb.id);
                              setShowKbDropdown(false);
                            }}
                            className={`w-full px-3 py-2 text-left text-sm hover:bg-gray-50 ${
                              currentSession.knowledge_base_id === kb.id
                                ? 'text-primary-600 bg-primary-50'
                                : 'text-text-secondary'
                            }`}
                          >
                            {kb.name}
                          </button>
                        ))
                      )}
                    </div>
                  )}
                </div>

                <div className="flex-1" />

                <span className="text-xs text-text-tertiary">
                  当前专家：{currentExpert?.name}
                </span>
              </div>

              {/* 输入框 */}
              <div className="flex items-end gap-3">
                <div className="flex-1 relative">
                  <textarea
                    ref={textareaRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={`向${currentExpert?.name}提问... (Enter发送，Shift+Enter换行)`}
                    className="w-full px-4 py-3 bg-bg-secondary rounded-xl text-text placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary-200 resize-none text-sm min-h-[48px] max-h-40"
                    rows={1}
                    disabled={loading.stream}
                  />
                </div>
                <Button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || loading.stream}
                  size="lg"
                >
                  {loading.stream ? (
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  )}
                  发送
                </Button>
              </div>
            </div>
          </>
        ) : (
          /* 未选择会话 */
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="w-24 h-24 mx-auto mb-6 bg-white rounded-2xl shadow-soft flex items-center justify-center text-5xl">
                👨‍💻
              </div>
              <h3 className="text-xl font-semibold text-text mb-2">技术专家组</h3>
              <p className="text-text-tertiary mb-6 max-w-md">
                多专家协作，从架构设计到测试验证，全流程助力您的项目开发
              </p>
              <Button size="lg" onClick={() => setShowNewSessionModal(true)}>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                开始新对话
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* 新建会话模态框 */}
      <Modal
        visible={showNewSessionModal}
        title="新建对话"
        onClose={() => setShowNewSessionModal(false)}
        footer={
          <>
            <Button variant="outline" onClick={() => setShowNewSessionModal(false)}>
              取消
            </Button>
            <Button onClick={handleCreateSession} disabled={!newSessionTitle.trim()}>
              创建
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="对话主题"
            placeholder="请输入对话主题"
            value={newSessionTitle}
            onChange={(e) => setNewSessionTitle(e.target.value)}
            required
            maxLength={100}
          />

          <div>
            <label className="block text-sm font-medium text-text mb-1.5">
              关联知识库（可选）
            </label>
            <select
              className="w-full h-10 px-4 border border-gray-200 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary-100 focus:border-primary-400 bg-white"
              value={newSessionKbId || ''}
              onChange={(e) => setNewSessionKbId(e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">不关联知识库</option>
              {knowledgeBases.map((kb) => (
                <option key={kb.id} value={kb.id}>
                  {kb.name}
                </option>
              ))}
            </select>
          </div>

          <div className="p-4 bg-primary-50 rounded-xl">
            <h4 className="font-medium text-primary-700 mb-2">工作流程</h4>
            <div className="flex items-center gap-2 text-sm text-primary-600">
              {phases.map((phase, index) => (
                <>
                  <span>{phase.icon} {phase.label}</span>
                  {index < phases.length - 1 && (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  )}
                </>
              ))}
            </div>
          </div>
        </div>
      </Modal>

      {/* 插入代码模态框 */}
      <Modal
        visible={showInsertCode}
        title="插入代码"
        onClose={() => setShowInsertCode(false)}
        width={600}
        footer={
          <>
            <Button variant="outline" onClick={() => setShowInsertCode(false)}>
              取消
            </Button>
            <Button onClick={handleInsertCode} disabled={!codeContent.trim()}>
              插入
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text mb-1.5">
              语言
            </label>
            <select
              className="w-full h-10 px-4 border border-gray-200 rounded-lg text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary-100 focus:border-primary-400 bg-white"
              value={codeLanguage}
              onChange={(e) => setCodeLanguage(e.target.value)}
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="java">Java</option>
              <option value="go">Go</option>
              <option value="rust">Rust</option>
              <option value="cpp">C++</option>
              <option value="sql">SQL</option>
              <option value="bash">Bash</option>
              <option value="json">JSON</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-text mb-1.5">
              代码内容
            </label>
            <textarea
              className="w-full h-48 px-4 py-3 border border-gray-200 rounded-lg font-mono text-sm text-text focus:outline-none focus:ring-2 focus:ring-primary-100 focus:border-primary-400 resize-none bg-gray-50"
              placeholder="粘贴代码..."
              value={codeContent}
              onChange={(e) => setCodeContent(e.target.value)}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
