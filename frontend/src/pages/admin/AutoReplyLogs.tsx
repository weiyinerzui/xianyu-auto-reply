/**
 * 自动回复日志页面
 *
 * 功能：
 * 1. 展示自动回复日志列表（支持分页、筛选）
 * 2. 统计概览（按策略、按发送状态）
 * 3. 查看日志详情
 */
import { useState, useEffect, useCallback } from 'react'
import { FileText, ChevronLeft, ChevronRight, Loader2, Filter } from 'lucide-react'
import {
  getAutoReplyLogs,
  getAutoReplyLogStats,
  type AutoReplyLog,
  type AutoReplyLogStats,
} from '@/api/autoReplyLogs'
import { useUIStore } from '@/store/uiStore'
import { PageLoading } from '@/components/common/Loading'
import { Select } from '@/components/common/Select'

const STRATEGY_LABELS: Record<string, string> = {
  keyword: '关键词',
  ai: 'AI回复',
  default: '默认回复',
  auto_delivery: '自动发货',
  none: '未回复',
}

const STATUS_LABELS: Record<string, string> = {
  success: '成功',
  failed: '失败',
  unknown: '待确认',
  timeout: '超时',
}

const STATUS_BADGES: Record<string, string> = {
  success: 'badge-success',
  failed: 'badge-error',
  unknown: 'badge-warning',
  timeout: 'badge-error',
}

const PAGE_SIZE = 20

export function AutoReplyLogs() {
  const { addToast } = useUIStore()
  const [logs, setLogs] = useState<AutoReplyLog[]>([])
  const [stats, setStats] = useState<AutoReplyLogStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [offset, setOffset] = useState(0)

  // 筛选
  const [filterStrategy, setFilterStrategy] = useState('')
  const [filterStatus, setFilterStatus] = useState('')

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true)
      const data = await getAutoReplyLogs({
        reply_strategy: filterStrategy || undefined,
        send_status: filterStatus || undefined,
        limit: PAGE_SIZE,
        offset,
      })
      setLogs(data.logs || [])
    } catch {
      addToast({ type: 'error', message: '获取日志失败' })
    } finally {
      setLoading(false)
    }
  }, [addToast, filterStrategy, filterStatus, offset])

  const fetchStats = useCallback(async () => {
    try {
      const data = await getAutoReplyLogStats()
      setStats(data.stats)
    } catch {
      // 静默失败
    }
  }, [])

  useEffect(() => {
    void fetchLogs()
  }, [fetchLogs])

  useEffect(() => {
    void fetchStats()
  }, [fetchStats])

  const handleFilterChange = () => {
    setOffset(0)
    void fetchLogs()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <FileText className="h-5 w-5 text-blue-500" />
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">自动回复日志</h1>
      </div>

      {/* 统计概览 */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="vben-card p-4">
            <p className="text-xs text-slate-500 dark:text-slate-400">总日志数</p>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">{stats.total}</p>
          </div>
          {Object.entries(stats.by_strategy).slice(0, 3).map(([key, count]) => (
            <div key={key} className="vben-card p-4">
              <p className="text-xs text-slate-500 dark:text-slate-400">{STRATEGY_LABELS[key] || key}</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-slate-100 mt-1">{count}</p>
            </div>
          ))}
        </div>
      )}

      {/* 筛选栏 */}
      <div className="vben-card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="h-4 w-4 text-slate-500" />
          <span className="text-sm font-medium text-slate-900 dark:text-slate-100">筛选</span>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="w-40">
            <Select
              value={filterStrategy}
              onChange={(v) => { setFilterStrategy(v); setTimeout(handleFilterChange, 0) }}
              options={[
                { value: '', label: '全部策略' },
                { value: 'keyword', label: '关键词' },
                { value: 'ai', label: 'AI回复' },
                { value: 'default', label: '默认回复' },
                { value: 'auto_delivery', label: '自动发货' },
                { value: 'none', label: '未回复' },
              ]}
            />
          </div>
          <div className="w-40">
            <Select
              value={filterStatus}
              onChange={(v) => { setFilterStatus(v); setTimeout(handleFilterChange, 0) }}
              options={[
                { value: '', label: '全部状态' },
                { value: 'success', label: '成功' },
                { value: 'failed', label: '失败' },
                { value: 'unknown', label: '待确认' },
                { value: 'timeout', label: '超时' },
              ]}
            />
          </div>
        </div>
      </div>

      {/* 日志列表 */}
      <div className="vben-card">
        {loading ? (
          <div className="p-8"><PageLoading /></div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center text-slate-400 dark:text-slate-500">暂无日志记录</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-700 text-slate-500 dark:text-slate-400">
                  <th className="text-left p-3 font-medium">时间</th>
                  <th className="text-left p-3 font-medium">策略</th>
                  <th className="text-left p-3 font-medium">发送状态</th>
                  <th className="text-left p-3 font-medium">消息</th>
                  <th className="text-left p-3 font-medium">回复</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr
                    key={log.id}
                    className="border-b border-slate-50 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                  >
                    <td className="p-3 text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
                      {log.created_at}
                    </td>
                    <td className="p-3">
                      <span className="badge badge-info">{STRATEGY_LABELS[log.reply_strategy] || log.reply_strategy}</span>
                    </td>
                    <td className="p-3">
                      <span className={`badge ${STATUS_BADGES[log.send_status] || 'badge-info'}`}>
                        {STATUS_LABELS[log.send_status] || log.send_status}
                      </span>
                    </td>
                    <td className="p-3 max-w-xs truncate text-slate-700 dark:text-slate-300" title={log.message_text || ''}>
                      {log.message_text || '-'}
                    </td>
                    <td className="p-3 max-w-xs truncate text-slate-700 dark:text-slate-300" title={log.reply_text || ''}>
                      {log.reply_text || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 分页 */}
        {!loading && logs.length > 0 && (
          <div className="flex items-center justify-between p-3 border-t border-slate-100 dark:border-slate-700">
            <span className="text-xs text-slate-500">
              第 {offset + 1} - {offset + logs.length} 条
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                disabled={offset === 0}
                className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={logs.length < PAGE_SIZE}
                className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
