/**
 * 知识库页面
 * 左侧知识库列表、顶部搜索栏、文档网格、上传模态框
 */

import { useState, useEffect, useRef } from 'react';
import { useKnowledgeStore } from '@/store/useKnowledgeStore';
import Button from '@/components/Common/Button';
import Input from '@/components/Common/Input';
import Modal from '@/components/Common/Modal';
import Loading from '@/components/Common/Loading';
import { formatFileSize, formatDate } from '@/utils/format';
import type { KnowledgeBase, Document, SearchResult } from '@/api/types';

export default function KnowledgeBase() {
  const {
    knowledgeBases,
    currentKnowledgeBase,
    documents,
    searchResults,
    loading,
    fetchKnowledgeBases,
    fetchDocuments,
    createBase,
    setCurrentKnowledgeBase,
    uploadDoc,
    search,
    clearSearchResults,
  } = useKnowledgeStore();

  // 本地状态
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [newKbName, setNewKbName] = useState('');
  const [newKbDesc, setNewKbDesc] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const searchTimerRef = useRef<number | null>(null);

  // 初始化加载知识库列表
  useEffect(() => {
    fetchKnowledgeBases();
  }, [fetchKnowledgeBases]);

  // 当选中知识库变化时，加载文档
  useEffect(() => {
    if (currentKnowledgeBase) {
      fetchDocuments(currentKnowledgeBase.id);
    }
  }, [currentKnowledgeBase?.id, fetchDocuments]);

  // 搜索防抖
  useEffect(() => {
    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }

    if (!searchQuery.trim()) {
      clearSearchResults();
      setIsSearching(false);
      return;
    }

    if (!currentKnowledgeBase) return;

    searchTimerRef.current = window.setTimeout(async () => {
      setIsSearching(true);
      await search({
        query: searchQuery,
        knowledge_base_id: currentKnowledgeBase.id,
      });
      setIsSearching(false);
    }, 500);

    return () => {
      if (searchTimerRef.current) {
        clearTimeout(searchTimerRef.current);
      }
    };
  }, [searchQuery, currentKnowledgeBase?.id, search, clearSearchResults]);

  // 创建知识库
  const handleCreateKb = async () => {
    if (!newKbName.trim()) return;

    try {
      const kb = await createBase({
        name: newKbName.trim(),
        description: newKbDesc.trim() || undefined,
      });
      setCurrentKnowledgeBase(kb);
      setShowCreateModal(false);
      setNewKbName('');
      setNewKbDesc('');
    } catch (error) {
      console.error('创建知识库失败:', error);
    }
  };

  // 选择文件
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadProgress(0);
    }
  };

  // 上传文件
  const handleUpload = async () => {
    if (!selectedFile || !currentKnowledgeBase) return;

    try {
      await uploadDoc(
        currentKnowledgeBase.id,
        selectedFile,
        (progress) => setUploadProgress(progress)
      );
      setShowUploadModal(false);
      setSelectedFile(null);
      setUploadProgress(0);
      // 刷新文档列表
      fetchDocuments(currentKnowledgeBase.id);
    } catch (error) {
      console.error('上传失败:', error);
    }
  };

  // 文件类型图标
  const getFileIcon = (fileType: string) => {
    const type = fileType.toLowerCase();
    if (type.includes('pdf')) return { icon: '📄', color: 'text-red-500' };
    if (type.includes('word') || type.includes('doc')) return { icon: '📝', color: 'text-blue-500' };
    if (type.includes('excel') || type.includes('xls') || type.includes('csv')) return { icon: '📊', color: 'text-green-500' };
    if (type.includes('ppt') || type.includes('powerpoint')) return { icon: '📽️', color: 'text-orange-500' };
    if (type.includes('text') || type.includes('txt') || type.includes('md')) return { icon: '📃', color: 'text-gray-500' };
    if (type.includes('image')) return { icon: '🖼️', color: 'text-purple-500' };
    return { icon: '📁', color: 'text-gray-500' };
  };

  return (
    <div className="h-full flex">
      {/* 左侧知识库列表 */}
      <div className="w-64 bg-white border-r border-gray-100 flex flex-col">
        <div className="p-4 border-b border-gray-50">
          <Button block size="sm" onClick={() => setShowCreateModal(true)}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新建知识库
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {loading.knowledgeBases ? (
            <div className="py-8">
              <Loading size="sm" />
            </div>
          ) : knowledgeBases.length === 0 ? (
            <div className="text-center py-8 text-text-tertiary text-sm">
              暂无知识库
            </div>
          ) : (
            <div className="space-y-1">
              {knowledgeBases.map((kb: KnowledgeBase) => (
                <button
                  key={kb.id}
                  onClick={() => setCurrentKnowledgeBase(kb)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    currentKnowledgeBase?.id === kb.id
                      ? 'bg-primary-50 text-primary-700'
                      : 'hover:bg-gray-50 text-text-secondary'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    <span className="font-medium truncate">{kb.name}</span>
                  </div>
                  <div className="text-xs text-text-tertiary ml-6">
                    {kb.document_count} 篇文档
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 右侧主内容区 */}
      <div className="flex-1 flex flex-col min-w-0">
        {currentKnowledgeBase ? (
          <>
            {/* 顶部工具栏 */}
            <div className="p-4 bg-white border-b border-gray-100">
              <div className="flex items-center gap-4">
                <div className="flex-1 relative">
                  <Input
                    type="text"
                    placeholder="搜索文档内容..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    leftIcon={
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    }
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
                <Button onClick={() => setShowUploadModal(true)}>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  上传文档
                </Button>
              </div>
            </div>

            {/* 内容区 */}
            <div className="flex-1 overflow-y-auto p-6 bg-bg">
              {/* 搜索结果 */}
              {searchQuery.trim() ? (
                <div>
                  <h3 className="text-lg font-semibold text-text mb-4">
                    搜索结果
                    {!isSearching && searchResults.length > 0 && (
                      <span className="text-sm font-normal text-text-tertiary ml-2">
                        找到 {searchResults.length} 条相关结果
                      </span>
                    )}
                  </h3>

                  {isSearching ? (
                    <div className="py-12">
                      <Loading text="搜索中..." />
                    </div>
                  ) : searchResults.length === 0 ? (
                    <div className="text-center py-12 text-text-tertiary">
                      未找到相关内容
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {searchResults.map((result: SearchResult) => {
                        const fileInfo = getFileIcon('text');
                        return (
                          <div
                            key={result.id}
                            className="bg-white rounded-xl p-5 shadow-soft hover:shadow-medium transition-shadow"
                          >
                            <div className="flex items-start gap-3 mb-3">
                              <span className="text-2xl">{fileInfo.icon}</span>
                              <div className="flex-1 min-w-0">
                                <h4 className="font-medium text-text truncate">
                                  {result.document_title}
                                </h4>
                                <div className="flex items-center gap-3 mt-1 text-xs text-text-tertiary">
                                  <span>第 {result.chunk_index + 1} 段</span>
                                  <span>相似度: {(result.similarity * 100).toFixed(1)}%</span>
                                </div>
                              </div>
                              <div className="px-2 py-1 bg-primary-50 text-primary-600 text-xs rounded-full">
                                {(result.similarity * 100).toFixed(0)}%
                              </div>
                            </div>
                            <p className="text-sm text-text-secondary leading-relaxed line-clamp-3">
                              {result.content}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ) : (
                /* 文档网格 */
                <div>
                  <h3 className="text-lg font-semibold text-text mb-4">
                    {currentKnowledgeBase.name}
                    <span className="text-sm font-normal text-text-tertiary ml-2">
                      共 {documents.length} 篇文档
                    </span>
                  </h3>

                  {loading.documents ? (
                    <div className="py-12">
                      <Loading text="加载中..." />
                    </div>
                  ) : documents.length === 0 ? (
                    <div className="text-center py-16">
                      <div className="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                        <svg className="w-10 h-10 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <p className="text-text-tertiary mb-4">暂无文档</p>
                      <Button onClick={() => setShowUploadModal(true)}>
                        上传第一个文档
                      </Button>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                      {documents.map((doc: Document) => {
                        const fileInfo = getFileIcon(doc.file_type);
                        return (
                          <div
                            key={doc.id}
                            className="bg-white rounded-xl p-4 shadow-soft hover:shadow-medium transition-all cursor-pointer group"
                          >
                            <div className="flex items-start gap-3 mb-3">
                              <span className="text-3xl">{fileInfo.icon}</span>
                              <div className="flex-1 min-w-0">
                                <h4 className="font-medium text-text truncate group-hover:text-primary-600 transition-colors">
                                  {doc.title}
                                </h4>
                                <p className="text-xs text-text-tertiary mt-0.5 truncate">
                                  {doc.file_name}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center justify-between text-xs text-text-tertiary">
                              <span>{formatFileSize(doc.file_size)}</span>
                              <span>{formatDate(doc.created_at, 'MM-DD')}</span>
                            </div>
                            {/* 处理状态 */}
                            {doc.status !== 'completed' && (
                              <div className="mt-2 pt-2 border-t border-gray-50">
                                {doc.status === 'processing' && (
                                  <span className="text-xs text-accent-600 flex items-center gap-1">
                                    <span className="w-1.5 h-1.5 bg-accent-500 rounded-full animate-pulse" />
                                    处理中
                                  </span>
                                )}
                                {doc.status === 'pending' && (
                                  <span className="text-xs text-text-tertiary">等待处理</span>
                                )}
                                {doc.status === 'failed' && (
                                  <span className="text-xs text-danger-500">处理失败</span>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        ) : (
          /* 未选择知识库 */
          <div className="flex-1 flex items-center justify-center bg-bg">
            <div className="text-center">
              <div className="w-24 h-24 mx-auto mb-6 bg-white rounded-2xl shadow-soft flex items-center justify-center">
                <svg className="w-12 h-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-text mb-2">选择或创建知识库</h3>
              <p className="text-text-tertiary mb-6">从左侧选择一个知识库，或创建新的知识库</p>
              <Button onClick={() => setShowCreateModal(true)}>
                创建知识库
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* 新建知识库模态框 */}
      <Modal
        visible={showCreateModal}
        title="新建知识库"
        onClose={() => setShowCreateModal(false)}
        footer={
          <>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              取消
            </Button>
            <Button onClick={handleCreateKb} disabled={!newKbName.trim()}>
              创建
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="知识库名称"
            placeholder="请输入知识库名称"
            value={newKbName}
            onChange={(e) => setNewKbName(e.target.value)}
            required
            maxLength={50}
          />
          <div>
            <label className="block text-sm font-medium text-text mb-1.5">
              描述（可选）
            </label>
            <textarea
              className="w-full h-24 px-4 py-3 border border-gray-200 rounded-lg text-sm text-text placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary-100 focus:border-primary-400 resize-none"
              placeholder="请输入知识库描述"
              value={newKbDesc}
              onChange={(e) => setNewKbDesc(e.target.value)}
              maxLength={200}
            />
          </div>
        </div>
      </Modal>

      {/* 上传文档模态框 */}
      <Modal
        visible={showUploadModal}
        title="上传文档"
        onClose={() => {
          setShowUploadModal(false);
          setSelectedFile(null);
          setUploadProgress(0);
        }}
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => {
                setShowUploadModal(false);
                setSelectedFile(null);
                setUploadProgress(0);
              }}
            >
              取消
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!selectedFile || loading.upload}
              loading={loading.upload}
            >
              上传
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {/* 拖拽上传区域 */}
          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
              selectedFile
                ? 'border-primary-300 bg-primary-50/30'
                : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={handleFileSelect}
              accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.md,.csv"
            />
            {selectedFile ? (
              <div>
                <div className="text-3xl mb-2">📄</div>
                <p className="font-medium text-text mb-1">{selectedFile.name}</p>
                <p className="text-sm text-text-tertiary">
                  {formatFileSize(selectedFile.size)}
                </p>
                {uploadProgress > 0 && (
                  <div className="mt-4">
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-500 rounded-full transition-all"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                    <p className="text-xs text-text-tertiary mt-1">{uploadProgress}%</p>
                  </div>
                )}
              </div>
            ) : (
              <div>
                <svg
                  className="w-12 h-12 mx-auto mb-3 text-gray-300"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                <p className="text-text-secondary mb-1">点击或拖拽文件到此处</p>
                <p className="text-xs text-text-tertiary">
                  支持 PDF、Word、Excel、PPT、TXT、Markdown 等格式
                </p>
              </div>
            )}
          </div>

          <p className="text-xs text-text-tertiary text-center">
            单个文件不超过 50MB
          </p>
        </div>
      </Modal>
    </div>
  );
}
