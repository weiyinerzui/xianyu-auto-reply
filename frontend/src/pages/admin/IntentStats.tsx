/**
 * 意图识别统计看板
 *
 * 功能：
 * 1. 按策略统计（keyword/ai/default/auto_delivery/none）
 * 2. 按发送状态统计（success/failed/unknown/timeout）
 * 3. 每日趋势（折线图替代为表格）
 * 4. 时间范围切换（7天/14天/30天）
 */
import { useState, useEffect, useCallback } from 'react'
import { Brain, Loader2, Calendar } from 'lucide-react'
import { getIntentStats, type IntentStats } from '@/api/intentStats'
import { useUIStore } from '@/store/uiStore'
import { PageLoading } from '@/components/common/Loading'
import { Select } from '@/components/common/Select'

const STRATEGY_LABELS: Record<string, string> = {
  keyword: '关键词',
  ai: 'AI回复',
  default: '默认回复',
  auto_delivery: '自动发货',
  none: '未回复',
  api: 'API回复',
  price: '议价',
  tech: '技术咨询',
}

const STRATEGY_COLORS: Record<string, string> = {
  keyword: 'bg-blue-500',
  ai: 'bg-purple-500',
  default: 'bg-green-500',
  auto_delivery: 'bg-orange-500',
  none: 'bg-gray-400',
  api: 'bg-cyan-500',
  price: 'bg-red-500',
  tech: 'bg-indigo-500',
}

const STATUS_LABELS: Record<string, string> = {
  success: '成功',
  failed: '失败',
  unknown: '待确认',
  timeout: '超时',
}

const STATUS_COLORS: Record<string, string> = {
  success: 'text-green-600',
  failed: 'text-red-600',
  unknown: 'text-yellow-600',
  timeout: 'text-red-600',
}

export function IntentStats() {
  const { addToast } = useUIStore()
  const [stats, setStats] = useState<IntentStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(7)

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true)
      const data = await getIntentStats(undefined, days)
      setStats(data.stats)
    } catch {
      addToast({ type: 'error', message: '获取意图统计失败' })
    } finally {
      setLoading(false)
    }
  }, [addToast, days])

  useEffect(() => {
    void fetchStats()
  }, [fetchStats])

  const maxStrategyCount = stats
    ? Math.max(...Object.values(stats.by_strategy), 1)
    : 1

  const sortedTrendDates = stats
    ? Object.keys(stats.daily_trend).sort()
    : []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-purple-500" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">意图识别统计</h1>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-slate-400" />
          <div className="w-32">
            <Select
              value={String(days)}
              onChange={(v) => setDays(parseInt(v))}
              options={[
                { value: '7', label: '最近7天' },
                { value: '14', label: '最近14天' },
                { value: '30', label: '最近30天' },
              ]}
            />
          </div>
        </div>
      </div>

      {loading ? (
        <PageLoading />
      ) : !stats || stats.total === 0 ? (
        <div className="vben-card p-8 text-center text-slate-400 dark:text-slate-500">
          暂无意图识别数据，启用AI回复后将自动统计
        </div>
      ) : (
        <>
          {/* 总数概览 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="vben-card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400">总消息数</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">{stats.total}</p>
            </div>
            {Object.entries(stats.by_strategy).slice(0, 3).map(([key, count]) => (
              <div key={key} className="vben-card p-4">
                <p className="text-xs text-slate-500 dark:text-slate-400">{STRATEGY_LABELS[key] || key}</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">{count}</p>
              </div>
            ))}
          </div>

          {/* 按策略分布 */}
          <div className="vben-card p-4">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">按回复策略分布</h2>
            <div className="space-y-3">
              {Object.entries(stats.by_strategy).map(([strategy, count]) => (
                <div key={strategy} className="flex items-center gap-3">
                  <span className="text-sm text-slate-600 dark:text-slate-400 w-20 shrink-0">
                    {STRATEGY_LABELS[strategy] || strategy}
                  </span>
                  <div className="flex-1 bg-slate-100 dark:bg-slate-800 rounded-full h-6 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${STRATEGY_COLORS[strategy] || 'bg-blue-500'}`}
                      style={{ width: `${(count / maxStrategyCount) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-100 w-12 text-right">
                    {count}
                  </span>
                  <span className="text-xs text-slate-400 w-10 text-right">
                    {((count / stats.total) * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* 按发送状态分布 */}
          <div className="vben-card p-4">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-4">按发送状态分布</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(stats.by_status).map(([status, count]) => (
                <div key={status} className="text-center p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
                  <p className="text-xs text-slate-500 dark:text-slate-400">{STATUS_LABELS[status] || status}</p>
                  <p className={`text-xl font-bold mt-1 ${STATUS_COLORS[status] || 'text-slate-700'}`}>{count}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 每日趋势 */}
          {sortedTrendDates.length > 0 && (
            <div className="vben-card">
              <div className="p-4 border-b border-slate-100 dark:border-slate-700">
                <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">每日趋势</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 dark:border-slate-700 text-slate-500 dark:text-slate-400">
                      <th className="text-left p-3 font-medium">日期</th>
                      {Object.keys(stats.by_strategy).map((s) => (
                        <th key={s} className="text-center p-3 font-medium">{STRATEGY_LABELS[s] || s}</th>
                      ))}
                      <th className="text-center p-3 font-medium">合计</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedTrendDates.map((date) => {
                      const dayData = stats.daily_trend[date]
                      const dayTotal = Object.values(dayData).reduce((a, b) => a + b, 0)
                      return (
                        <tr key={date} className="border-b border-slate-50 dark:border-slate-800">
                          <td className="p-3 text-slate-600 dark:text-slate-400 whitespace-nowrap">{date}</td>
                          {Object.keys(stats.by_strategy).map((s) => (
                            <td key={s} className="text-center p-3 text-slate-700 dark:text-slate-300">
                              {dayData[s] || 0}
                            </td>
                          ))}
                          <td className="text-center p-3 font-medium text-slate-900 dark:text-slate-100">{dayTotal}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
