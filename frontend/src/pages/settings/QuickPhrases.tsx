/**
 * 快捷短语管理页面
 *
 * 功能：
 * 1. 展示快捷短语列表（标题 + 内容 + 排序）
 * 2. 添加/编辑/删除短语
 * 3. 拖拽排序（简化为数字输入）
 */
import { useState, useEffect, useCallback } from 'react'
import { MessageCircle, Plus, Trash2, Edit2, X, Loader2, Save } from 'lucide-react'
import {
  getQuickPhrases,
  createQuickPhrase,
  updateQuickPhrase,
  deleteQuickPhrase,
  type QuickPhrase,
} from '@/api/quickPhrases'
import { useUIStore } from '@/store/uiStore'
import { PageLoading } from '@/components/common/Loading'

export function QuickPhrases() {
  const { addToast } = useUIStore()
  const [phrases, setPhrases] = useState<QuickPhrase[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // 弹窗
  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [sortOrder, setSortOrder] = useState(0)

  const fetchPhrases = useCallback(async () => {
    try {
      const data = await getQuickPhrases()
      setPhrases(data.phrases || [])
    } catch {
      addToast({ type: 'error', message: '获取快捷短语失败' })
    } finally {
      setLoading(false)
    }
  }, [addToast])

  useEffect(() => {
    void fetchPhrases()
  }, [fetchPhrases])

  const openAdd = () => {
    setEditingId(null)
    setTitle('')
    setContent('')
    setSortOrder(0)
    setModalOpen(true)
  }

  const openEdit = (phrase: QuickPhrase) => {
    setEditingId(phrase.id)
    setTitle(phrase.title)
    setContent(phrase.content)
    setSortOrder(phrase.sort_order)
    setModalOpen(true)
  }

  const closeModal = () => {
    setModalOpen(false)
    setEditingId(null)
  }

  const handleSave = async () => {
    if (!title.trim() || !content.trim()) {
      addToast({ type: 'error', message: '标题和内容不能为空' })
      return
    }
    setSaving(true)
    try {
      if (editingId) {
        await updateQuickPhrase(editingId, {
          title: title.trim(),
          content: content.trim(),
          sort_order: sortOrder,
        })
        addToast({ type: 'success', message: '快捷短语已更新' })
      } else {
        await createQuickPhrase({
          title: title.trim(),
          content: content.trim(),
          sort_order: sortOrder,
        })
        addToast({ type: 'success', message: '快捷短语已添加' })
      }
      closeModal()
      void fetchPhrases()
    } catch {
      addToast({ type: 'error', message: '保存失败' })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteQuickPhrase(id)
      setPhrases((prev) => prev.filter((p) => p.id !== id))
      addToast({ type: 'success', message: '已删除' })
    } catch {
      addToast({ type: 'error', message: '删除失败' })
    }
  }

  if (loading) return <PageLoading />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageCircle className="h-5 w-5 text-blue-500" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">快捷短语</h1>
        </div>
        <button onClick={openAdd} className="btn-ios-primary">
          <Plus className="h-4 w-4" />
          添加短语
        </button>
      </div>

      {/* 短语列表 */}
      {phrases.length === 0 ? (
        <div className="vben-card p-8 text-center text-slate-400 dark:text-slate-500">
          暂无快捷短语，点击右上角添加
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {phrases.map((phrase) => (
            <div
              key={phrase.id}
              className="vben-card p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="font-medium text-slate-900 dark:text-slate-100 truncate">
                  {phrase.title}
                </h3>
                <div className="flex gap-1 shrink-0">
                  <button
                    onClick={() => openEdit(phrase)}
                    className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                    title="编辑"
                  >
                    <Edit2 className="h-3.5 w-3.5 text-slate-400" />
                  </button>
                  <button
                    onClick={() => void handleDelete(phrase.id)}
                    className="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                    title="删除"
                  >
                    <Trash2 className="h-3.5 w-3.5 text-red-500" />
                  </button>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-3 whitespace-pre-wrap">
                {phrase.content}
              </p>
              {phrase.sort_order !== 0 && (
                <span className="inline-block mt-2 text-xs text-slate-400">
                  排序: {phrase.sort_order}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 添加/编辑弹窗 */}
      {modalOpen && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content max-w-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                {editingId ? '编辑快捷短语' : '添加快捷短语'}
              </h2>
              <button onClick={closeModal} className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">
                <X className="h-4 w-4 text-slate-500" />
              </button>
            </div>
            <div className="modal-body space-y-4">
              <div>
                <label className="input-label">标题 <span className="text-red-500">*</span></label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="input-ios"
                  placeholder="例如：欢迎语、发货说明"
                  maxLength={80}
                />
              </div>
              <div>
                <label className="input-label">内容 <span className="text-red-500">*</span></label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="input-ios h-32"
                  placeholder="输入短语内容..."
                  maxLength={2000}
                />
              </div>
              <div>
                <label className="input-label">排序值（越小越靠前）</label>
                <input
                  type="number"
                  value={sortOrder}
                  onChange={(e) => setSortOrder(parseInt(e.target.value) || 0)}
                  className="input-ios w-24"
                  min={0}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={closeModal} className="btn-ios-secondary">
                取消
              </button>
              <button
                onClick={() => void handleSave()}
                disabled={saving}
                className="btn-ios-primary"
              >
                {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                {editingId ? '更新' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
