/**
 * 微信公众号写作助手页面
 * 左侧会话列表、顶部状态进度条、中间输出区域、底部操作区
 */

import { useState, useEffect, useRef } from 'react';
import { useWeChatWriterStore, WRITER_PHASES, getPhaseProgress, getExpertForState, WRITER_EXPERTS } from '@/store/useWeChatWriterStore';
import Button from '@/components/Common/Button';
import Modal from '@/components/Common/Modal';
import Input from '@/components/Common/Input';
import MarkdownRender from '@/components/MarkdownRender';
import { formatDate } from '@/utils/format';
import type { WriterState, WriterSession } from '@/api/types';

export default function WeChatWriter() {
  const {
    sessions,
    currentSession,
    outputs,
    loading,
    fetchSessions,
    createSessionItem,
    setCurrentSession,
    fetchSession,
    fetchOutputs,
    doStartWriting,
    doConfirm,
    doRegenerate,
    doRollback,
  } = useWeChatWriterStore();

  // 弹窗状态
  const [showNewSessionModal, setShowNewSessionModal] = useState(false);
  const [newSessionTopic, setNewSessionTopic] = useState('');
  const [newSessionTitle, setNewSessionTitle] = useState('');

  // 重新生成弹窗
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [regenerateFeedback, setRegenerateFeedback] = useState('');

  // 回退弹窗
  const [showRollbackModal, setShowRollbackModal] = useState(false);
  const [rollbackTarget, setRollbackTarget] = useState<WriterState>('idle');
  const [rollbackReason, setRollbackReason] = useState('');

  const outputEndRef = useRef<HTMLDivElement>(null);

  // 初始化：加载会话列表
  useEffect(() => {
    fetchSessions();
  }, []);

  // 选择会话时加载详情和输出
  useEffect(() => {
    if (currentSession) {
      fetchOutputs(currentSession.id);
    }
  }, [currentSession?.id]);

  // 自动滚动到底部
  useEffect(() => {
    outputEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [outputs]);

  // ==================== 会话操作 ====================

  const handleCreateSession = async () => {
    if (!newSessionTopic.trim()) return;
    try {
      await createSessionItem({
        topic: newSessionTopic.trim(),
        title: newSessionTitle.trim() || undefined,
      });
      setShowNewSessionModal(false);
      setNewSessionTopic('');
      setNewSessionTitle('');
    } catch (error) {
      console.error('创建会话失败:', error);
    }
  };

  const handleSelectSession = async (session: WriterSession) => {
    setCurrentSession(session);
    await fetchSession(session.id);
  };

  // ==================== 状态操作 ====================

  const handleStartWriting = async () => {
    if (!currentSession) return;
    try {
      await doStartWriting(currentSession.id);
    } catch (error) {
      console.error('开始写作失败:', error);
    }
  };

  const handleConfirm = async () => {
    if (!currentSession) return;
    try {
      await doConfirm(currentSession.id);
    } catch (error) {
      console.error('确认失败:', error);
    }
  };

  const handleRegenerate = async () => {
    if (!currentSession) return;
    try {
      await doRegenerate(currentSession.id, regenerateFeedback.trim() || undefined);
      setShowRegenerateModal(false);
      setRegenerateFeedback('');
    } catch (error) {
      console.error('重新生成失败:', error);
    }
  };

  const handleRollback = async () => {
    if (!currentSession) return;
    try {
      await doRollback(currentSession.id, rollbackTarget, rollbackReason.trim() || undefined);
      setShowRollbackModal(false);
      setRollbackReason('');
    } catch (error) {
      console.error('回退失败:', error);
    }
  };

  // ==================== 辅助函数 ====================

  const getCurrentOutput = () => {
    if (!currentSession) return null;
    const stepMap: Record<string, string> = {
      topic_confirm: 'topic',
      research: 'research',
      outline: 'outline',
      draft: 'draft',
      polish: 'polish',
    };
    const step = stepMap[currentSession.current_state];
    if (!step) return null;
    const stepOutputs = outputs.filter(o => o.step === step);
    if (stepOutputs.length === 0) return null;
    return stepOutputs.reduce((latest, o) => o.version > latest.version ? o : latest);
  };

  const phaseProgress = currentSession ? getPhaseProgress(currentSession.current_state) : [];
  const currentExpert = currentSession ? WRITER_EXPERTS.find(e => e.key === getExpertForState(currentSession.current_state)) : null;
  const currentOutput = getCurrentOutput();

  // ==================== 渲染 ====================

  return (
    <div className="h-full flex flex-col bg-bg">
      <div className="flex-1 flex min-h-0">
        {/* 左侧会话列表 */}
        <div className="w-72 bg-white border-r border-gray-100 flex flex-col">
          <div className="p-4 border-b border-gray-50">
            <Button
              variant="primary"
              size="md"
              fullWidth
              onClick={() => setShowNewSessionModal(true)}
            >
              + 新建写作
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {sessions.length === 0 ? (
              <div className="text-center text-text-tertiary py-8 text-sm">
                暂无写作会话<br />
                点击上方按钮新建
              </div>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => handleSelectSession(session)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    currentSession?.id === session.id
                      ? 'bg-primary-50 border border-primary-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="font-medium text-text text-sm truncate">
                    {session.title}
                  </div>
                  <div className="text-xs text-text-tertiary mt-1 truncate">
                    {session.topic}
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      session.current_state === 'done'
                        ? 'bg-green-100 text-green-700'
                        : session.current_state === 'idle'
                        ? 'bg-gray-100 text-gray-600'
                        : 'bg-primary-100 text-primary-700'
                    }`}>
                      {WRITER_PHASES.find(p => p.key === session.current_state)?.label || session.current_state}
                    </span>
                    <span className="text-xs text-text-tertiary">
                      {formatDate(session.updated_at)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 右侧主内容区 */}
        <div className="flex-1 flex flex-col min-w-0">
          {!currentSession ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">✍️</div>
                <div className="text-text text-lg font-medium mb-2">开始你的公众号写作</div>
                <div className="text-text-tertiary text-sm mb-6">
                  从左侧选择一个会话，或新建一个写作任务
                </div>
                <Button variant="primary" onClick={() => setShowNewSessionModal(true)}>
                  新建写作
                </Button>
              </div>
            </div>
          ) : (
            <>
              {/* 顶部状态进度条 */}
              <div className="bg-white border-b border-gray-100 px-6 py-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h2 className="text-lg font-semibold text-text">{currentSession.title}</h2>
                    <p className="text-sm text-text-tertiary mt-1">{currentSession.topic}</p>
                  </div>
                  {currentExpert && (
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${currentExpert.color} text-white text-sm`}>
                      <span>{currentExpert.avatar}</span>
                      <span>{currentExpert.name}</span>
                    </div>
                  )}
                </div>

                {/* 阶段进度 */}
                <div className="flex items-center gap-1">
                  {phaseProgress.map((p, idx) => (
                    <div key={p.phase} className="flex items-center">
                      <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm ${
                        p.status === 'completed'
                          ? 'bg-green-50 text-green-700'
                          : p.status === 'current'
                          ? 'bg-primary-100 text-primary-700 font-medium'
                          : 'bg-gray-50 text-text-tertiary'
                      }`}>
                        <span>{WRITER_PHASES.find(ph => ph.key === p.phase)?.icon}</span>
                        <span>{p.label}</span>
                      </div>
                      {idx < phaseProgress.length - 1 && (
                        <div className={`w-6 h-0.5 mx-1 ${
                          p.status === 'completed' ? 'bg-green-300' : 'bg-gray-200'
                        }`} />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* 输出内容区 */}
              <div className="flex-1 overflow-y-auto p-6">
                {currentSession.current_state === 'idle' ? (
                  <div className="flex flex-col items-center justify-center h-full">
                    <div className="text-5xl mb-4">🎯</div>
                    <div className="text-text text-lg font-medium mb-2">准备开始写作</div>
                    <div className="text-text-tertiary text-sm mb-6 max-w-md text-center">
                      点击下方按钮，选题编辑将帮你分析主题、拆解需求、给出写作角度建议
                    </div>
                    <Button
                      variant="primary"
                      size="lg"
                      loading={loading.start}
                      onClick={handleStartWriting}
                    >
                      开始选题分析
                    </Button>
                  </div>
                ) : currentOutput ? (
                  <div className="max-w-4xl mx-auto">
                    {/* 输出版本标签 */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-1 bg-gray-100 text-text-secondary text-xs rounded">
                          v{currentOutput.version}
                        </span>
                        {currentOutput.feedback && (
                          <span className="px-2 py-1 bg-amber-50 text-amber-700 text-xs rounded">
                            含修改建议
                          </span>
                        )}
                        {currentOutput.is_confirmed && (
                          <span className="px-2 py-1 bg-green-50 text-green-700 text-xs rounded">
                            已确认
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Markdown 渲染 */}
                    <div className="bg-white rounded-xl border border-gray-100 p-6">
                      <MarkdownRender content={currentOutput.content} />
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-text-tertiary">暂无输出内容</div>
                  </div>
                )}
                <div ref={outputEndRef} />
              </div>

              {/* 底部操作区 */}
              {currentSession.current_state !== 'idle' && currentSession.current_state !== 'done' && (
                <div className="bg-white border-t border-gray-100 px-6 py-4">
                  <div className="flex items-center justify-between max-w-4xl mx-auto">
                    <div className="flex items-center gap-3">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setShowRegenerateModal(true)}
                        loading={loading.regenerate}
                      >
                        🔄 重新生成
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setShowRollbackModal(true)}
                        loading={loading.rollback}
                      >
                        ↩️ 回退
                      </Button>
                    </div>
                    <Button
                      variant="primary"
                      size="md"
                      onClick={handleConfirm}
                      loading={loading.confirm}
                    >
                      确认并继续 →
                    </Button>
                  </div>
                </div>
              )}

              {currentSession.current_state === 'done' && (
                <div className="bg-white border-t border-gray-100 px-6 py-4">
                  <div className="flex items-center justify-center max-w-4xl mx-auto gap-4">
                    <div className="text-green-600 font-medium">🎉 写作已完成！</div>
                    <Button variant="secondary" size="sm">
                      导出文章
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* 新建会话弹窗 */}
      <Modal
        open={showNewSessionModal}
        onClose={() => setShowNewSessionModal(false)}
        title="新建写作"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text mb-1.5">
              文章主题 <span className="text-danger-500">*</span>
            </label>
            <Input
              value={newSessionTopic}
              onChange={(e) => setNewSessionTopic(e.target.value)}
              placeholder="例如：人工智能对未来工作的影响"
              fullWidth
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text mb-1.5">
              会话标题（可选）
            </label>
            <Input
              value={newSessionTitle}
              onChange={(e) => setNewSessionTitle(e.target.value)}
              placeholder="默认使用主题作为标题"
              fullWidth
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={() => setShowNewSessionModal(false)}>
              取消
            </Button>
            <Button
              variant="primary"
              onClick={handleCreateSession}
              disabled={!newSessionTopic.trim()}
            >
              创建
            </Button>
          </div>
        </div>
      </Modal>

      {/* 重新生成弹窗 */}
      <Modal
        open={showRegenerateModal}
        onClose={() => setShowRegenerateModal(false)}
        title="重新生成"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text mb-1.5">
              修改建议（可选）
            </label>
            <textarea
              value={regenerateFeedback}
              onChange={(e) => setRegenerateFeedback(e.target.value)}
              placeholder="例如：分析得太泛了，请更加聚焦在知识工作者这个群体，结合具体职业案例"
              className="w-full h-32 px-3 py-2 border border-gray-200 rounded-lg text-sm text-text placeholder:text-text-tertiary focus:outline-none focus:border-primary-300 focus:ring-2 focus:ring-primary-100 resize-none"
            />
            <p className="text-xs text-text-tertiary mt-1.5">
              留空则 AI 自动换角度重新生成
            </p>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={() => setShowRegenerateModal(false)}>
              取消
            </Button>
            <Button variant="primary" onClick={handleRegenerate}>
              重新生成
            </Button>
          </div>
        </div>
      </Modal>

      {/* 回退弹窗 */}
      <Modal
        open={showRollbackModal}
        onClose={() => setShowRollbackModal(false)}
        title="回退到上一阶段"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text mb-2">
              选择回退目标 <span className="text-danger-500">*</span>
            </label>
            <div className="space-y-2">
              {phaseProgress
                .filter(p => p.status === 'completed')
                .map(p => (
                  <label
                    key={p.phase}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      rollbackTarget === p.phase
                        ? 'border-primary-300 bg-primary-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="rollbackTarget"
                      value={p.phase}
                      checked={rollbackTarget === p.phase}
                      onChange={() => setRollbackTarget(p.phase)}
                      className="text-primary-500"
                    />
                    <span className="text-sm">
                      {WRITER_PHASES.find(ph => ph.key === p.phase)?.icon}{' '}
                      {p.label}
                    </span>
                  </label>
                ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-text mb-1.5">
              回退原因（可选）
            </label>
            <Input
              value={rollbackReason}
              onChange={(e) => setRollbackReason(e.target.value)}
              placeholder="例如：选题还需要再细化一下"
              fullWidth
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={() => setShowRollbackModal(false)}>
              取消
            </Button>
            <Button
              variant="primary"
              onClick={handleRollback}
              disabled={!rollbackTarget}
            >
              确认回退
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
