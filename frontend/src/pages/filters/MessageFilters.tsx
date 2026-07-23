/**
 * 消息过滤规则管理页面
 *
 * 功能：
 * 1. 展示过滤规则列表（买家ID / 关键词 / 商品ID）
 * 2. 添加/删除规则
 * 3. 启用/禁用规则
 */
import { useState, useEffect, useCallback } from 'react'
import { Shield, Plus, Trash2, Loader2, Filter } from 'lucide-react'
import {
  getMessageFilters,
  createMessageFilter,
  updateMessageFilter,
  deleteMessageFilter,
  type MessageFilter,
} from '@/api/messageFilters'
import { useUIStore } from '@/store/uiStore'
import { PageLoading } from '@/components/common/Loading'
import { Select } from '@/components/common/Select'

const FILTER_TYPE_OPTIONS = [
  { value: 'buyer_id', label: '买家ID' },
  { value: 'keyword', label: '关键词' },
  { value: 'item_id', label: '商品ID' },
]

const FILTER_TYPE_LABELS: Record<string, string> = {
  buyer_id: '买家ID',
  keyword: '关键词',
  item_id: '商品ID',
}

const FILTER_TYPE_BADGES: Record<string, string> = {
  buyer_id: 'badge-error',
  keyword: 'badge-warning',
  item_id: 'badge-info',
}

export function MessageFilters() {
  const { addToast } = useUIStore()
  const [filters, setFilters] = useState<MessageFilter[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // 添加表单
  const [newType, setNewType] = useState('keyword')
  const [newValue, setNewValue] = useState('')
  const [newDesc, setNewDesc] = useState('')

  const fetchFilters = useCallback(async () => {
    try {
      const data = await getMessageFilters()
      setFilters(data.filters || [])
    } catch {
      addToast({ type: 'error', message: '获取过滤规则失败' })
    } finally {
      setLoading(false)
    }
  }, [addToast])

  useEffect(() => {
    void fetchFilters()
  }, [fetchFilters])

  const handleAdd = async () => {
    if (!newValue.trim()) {
      addToast({ type: 'error', message: '请输入过滤值' })
      return
    }
    setSaving(true)
    try {
      await createMessageFilter({
        filter_type: newType,
        filter_value: newValue.trim(),
        description: newDesc.trim() || undefined,
      })
      addToast({ type: 'success', message: '过滤规则已添加' })
      setNewValue('')
      setNewDesc('')
      void fetchFilters()
    } catch {
      addToast({ type: 'error', message: '添加失败' })
    } finally {
      setSaving(false)
    }
  }

  const handleToggle = async (filter: MessageFilter) => {
    try {
      await updateMessageFilter(filter.id, { enabled: !filter.enabled })
      setFilters((prev) =>
        prev.map((f) =>
          f.id === filter.id ? { ...f, enabled: !f.enabled } : f,
        ),
      )
    } catch {
      addToast({ type: 'error', message: '更新失败' })
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteMessageFilter(id)
      setFilters((prev) => prev.filter((f) => f.id !== id))
      addToast({ type: 'success', message: '已删除' })
    } catch {
      addToast({ type: 'error', message: '删除失败' })
    }
  }

  if (loading) return <PageLoading />

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Shield className="h-5 w-5 text-blue-500" />
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">消息过滤</h1>
      </div>

      {/* 添加规则 */}
      <div className="vben-card p-4">
        <div className="flex items-center gap-2 mb-3">
          <Plus className="h-4 w-4 text-slate-500" />
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">添加过滤规则</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="input-label">过滤类型</label>
            <Select value={newType} onChange={setNewType} options={FILTER_TYPE_OPTIONS} />
          </div>
          <div className="md:col-span-2">
            <label className="input-label">过滤值</label>
            <input
              type="text"
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  void handleAdd()
                }
              }}
              className="input-ios"
              placeholder={
                newType === 'buyer_id'
                  ? '输入买家ID，如：2215xxxxx'
                  : newType === 'item_id'
                    ? '输入商品ID，如：1048125657285'
                    : '输入关键词，如：广告'
              }
            />
          </div>
          <div>
            <label className="input-label">备注（可选）</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                className="input-ios"
                placeholder="备注"
              />
              <button
                onClick={() => void handleAdd()}
                disabled={saving || !newValue.trim()}
                className="btn-ios-primary whitespace-nowrap"
              >
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 规则列表 */}
      <div className="vben-card">
        <div className="flex items-center gap-2 p-4 border-b border-slate-100 dark:border-slate-700">
          <Filter className="h-4 w-4 text-slate-500" />
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            过滤规则列表 ({filters.length})
          </h2>
        </div>
        {filters.length === 0 ? (
          <div className="p-8 text-center text-slate-400 dark:text-slate-500">
            暂无过滤规则
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-700 text-slate-500 dark:text-slate-400">
                  <th className="text-left p-3 font-medium">类型</th>
                  <th className="text-left p-3 font-medium">过滤值</th>
                  <th className="text-left p-3 font-medium">备注</th>
                  <th className="text-center p-3 font-medium">启用</th>
                  <th className="text-center p-3 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {filters.map((filter) => (
                  <tr
                    key={filter.id}
                    className="border-b border-slate-50 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                  >
                    <td className="p-3">
                      <span className={`badge ${FILTER_TYPE_BADGES[filter.filter_type] || 'badge-info'}`}>
                        {FILTER_TYPE_LABELS[filter.filter_type] || filter.filter_type}
                      </span>
                    </td>
                    <td className="p-3">
                      <code className="text-slate-700 dark:text-slate-300">{filter.filter_value}</code>
                    </td>
                    <td className="p-3 text-slate-500 dark:text-slate-400">
                      {filter.description || '-'}
                    </td>
                    <td className="p-3 text-center">
                      <label className="switch-ios">
                        <input
                          type="checkbox"
                          checked={filter.enabled}
                          onChange={() => void handleToggle(filter)}
                        />
                        <span className="switch-slider"></span>
                      </label>
                    </td>
                    <td className="p-3 text-center">
                      <button
                        onClick={() => void handleDelete(filter.id)}
                        className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                        title="删除"
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
