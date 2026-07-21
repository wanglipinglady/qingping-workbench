/**
 * 工作台首页
 * 欢迎横幅、数据统计卡片、功能模块入口、最近访问列表
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useKnowledgeStore } from '@/store/useKnowledgeStore';
import { useUserStore } from '@/store/useUserStore';
import { formatDate } from '@/utils/format';
import Loading, { PageSkeleton } from '@/components/Common/Loading';

export default function Home() {
  const navigate = useNavigate();
  const { user } = useUserStore();
  const { stats, recentVisits, loading, fetchStats, fetchRecentVisits } = useKnowledgeStore();

  useEffect(() => {
    fetchStats();
    fetchRecentVisits();
  }, [fetchStats, fetchRecentVisits]);

  // 统计卡片数据
  const statCards = [
    {
      title: '知识库数量',
      value: stats?.knowledge_base_count ?? 0,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      ),
      color: 'bg-primary-50 text-primary-600',
      bgColor: 'bg-primary-100',
    },
    {
      title: '文档数量',
      value: stats?.document_count ?? 0,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      color: 'bg-accent-50 text-accent-600',
      bgColor: 'bg-accent-100',
    },
    {
      title: '对话数量',
      value: stats?.conversation_count ?? 0,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      ),
      color: 'bg-purple-50 text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: '调用次数',
      value: stats?.api_call_count ?? 0,
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      color: 'bg-danger-50 text-danger-600',
      bgColor: 'bg-danger-100',
    },
  ];

  // 功能模块
  const modules = [
    {
      title: '知识库',
      description: '管理文档，智能检索',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      ),
      color: 'from-primary-500 to-primary-600',
      path: '/knowledge',
      active: true,
    },
    {
      title: '技术专家组',
      description: '多专家协作，迭代开发',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      color: 'from-purple-500 to-purple-600',
      path: '/tech-experts',
      active: true,
    },
    {
      title: '项目管理',
      description: '任务追踪，团队协作',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
      ),
      color: 'from-gray-400 to-gray-500',
      path: '#',
      active: false,
    },
    {
      title: '数据分析',
      description: '数据洞察，智能报表',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      color: 'from-gray-400 to-gray-500',
      path: '#',
      active: false,
    },
  ];

  const handleModuleClick = (module: typeof modules[0]) => {
    if (module.active) {
      navigate(module.path);
    }
  };

  return (
    <div className="p-6">
      {loading.stats ? (
        <PageSkeleton />
      ) : (
        <>
          {/* 欢迎横幅 */}
          <div className="mb-6 p-6 bg-gradient-to-r from-primary-500 to-primary-600 rounded-2xl text-white relative overflow-hidden">
            <div className="relative z-10">
              <h2 className="text-2xl font-bold mb-2">
                欢迎回来，{user?.nickname || user?.username || '用户'}！
              </h2>
              <p className="text-primary-100">
                {formatDate(new Date(), 'YYYY年MM月DD日 dddd')} · 今天也是充满创造力的一天
              </p>
            </div>
            {/* 装饰图形 */}
            <div className="absolute right-0 top-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/4" />
            <div className="absolute right-20 bottom-0 w-32 h-32 bg-white/5 rounded-full translate-y-1/2" />
          </div>

          {/* 数据统计卡片 */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {statCards.map((card, index) => (
              <div
                key={index}
                className="bg-white rounded-xl p-5 shadow-soft hover:shadow-medium transition-shadow"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-text-secondary text-sm">{card.title}</span>
                  <div className={`p-2 rounded-lg ${card.color}`}>
                    {card.icon}
                  </div>
                </div>
                <div className="text-2xl font-bold text-text">
                  {card.value.toLocaleString()}
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 功能模块入口 */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-xl p-6 shadow-soft">
                <h3 className="text-lg font-semibold text-text mb-4">功能模块</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {modules.map((module, index) => (
                    <button
                      key={index}
                      onClick={() => handleModuleClick(module)}
                      disabled={!module.active}
                      className={`group p-4 rounded-xl border transition-all text-left ${
                        module.active
                          ? 'border-gray-100 hover:border-primary-200 hover:shadow-medium cursor-pointer'
                          : 'border-gray-100 opacity-50 cursor-not-allowed'
                      }`}
                    >
                      <div
                        className={`w-14 h-14 rounded-xl bg-gradient-to-br ${module.color} text-white flex items-center justify-center mb-3 group-hover:scale-105 transition-transform`}
                      >
                        {module.icon}
                      </div>
                      <div className="font-medium text-text mb-1">{module.title}</div>
                      <div className="text-xs text-text-tertiary">{module.description}</div>
                      {!module.active && (
                        <div className="mt-2 text-xs text-text-tertiary">即将上线</div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* 最近访问 */}
            <div className="bg-white rounded-xl p-6 shadow-soft">
              <h3 className="text-lg font-semibold text-text mb-4">最近访问</h3>
              {recentVisits.length === 0 ? (
                <div className="text-center py-8 text-text-tertiary text-sm">
                  暂无访问记录
                </div>
              ) : (
                <div className="space-y-3">
                  {recentVisits.map((visit) => (
                    <div
                      key={visit.id}
                      className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        visit.type === 'knowledge_base'
                          ? 'bg-primary-50 text-primary-600'
                          : 'bg-purple-50 text-purple-600'
                      }`}>
                        {visit.type === 'knowledge_base' ? (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-text truncate">
                          {visit.title}
                        </div>
                        <div className="text-xs text-text-tertiary">
                          {formatDate(visit.visited_at, 'MM-DD HH:mm')}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
