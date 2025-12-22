import { useState, useEffect } from 'react'
import { Save, X, FileText, Download, Upload, Copy, Check } from 'lucide-react'
import { useUIStore } from '@/store/uiStore'

interface KnowledgeBaseEditorProps {
    cookieId: string
    itemId: string
    itemTitle?: string
    onClose: () => void
    onSaved?: () => void
}

export function KnowledgeBaseEditor({ cookieId, itemId, itemTitle, onClose, onSaved }: KnowledgeBaseEditorProps) {
    const { addToast } = useUIStore()
    const [knowledgeBase, setKnowledgeBase] = useState('')
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [templates, setTemplates] = useState<Record<string, any>>({})
    const [selectedTemplate, setSelectedTemplate] = useState('')
    const [showTemplates, setShowTemplates] = useState(false)
    const [copied, setCopied] = useState(false)

    useEffect(() => {
        loadKnowledgeBase()
        loadTemplates()
    }, [cookieId, itemId])

    const loadKnowledgeBase = async () => {
        try {
            const response = await fetch(`/items/${cookieId}/${itemId}/knowledge-base`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                }
            })
            const data = await response.json()
            if (data.success) {
                setKnowledgeBase(data.knowledge_base || '')
            }
        } catch (error) {
            addToast({ type: 'error', message: '加载知识库失败' })
        } finally {
            setLoading(false)
        }
    }

    const loadTemplates = async () => {
        try {
            const response = await fetch('/knowledge-base/templates', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                }
            })
            const data = await response.json()
            if (data.success) {
                setTemplates(data.templates || {})
            }
        } catch (error) {
            console.error('加载模板失败:', error)
        }
    }

    const handleSave = async () => {
        try {
            setSaving(true)
            const response = await fetch(`/items/${cookieId}/${itemId}/knowledge-base`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                },
                body: JSON.stringify({ knowledge_base: knowledgeBase })
            })

            const data = await response.json()
            if (data.success) {
                addToast({ type: 'success', message: '知识库保存成功' })
                onSaved?.()
                onClose()
            } else {
                addToast({ type: 'error', message: data.message || '保存失败' })
            }
        } catch (error) {
            addToast({ type: 'error', message: '保存知识库失败' })
        } finally {
            setSaving(false)
        }
    }

    const handleUseTemplate = (templateKey: string) => {
        const template = templates[templateKey]
        if (template) {
            setKnowledgeBase(template.content)
            setSelectedTemplate(templateKey)
            setShowTemplates(false)
            addToast({ type: 'success', message: `已应用「${template.name}」模板` })
        }
    }

    const handleCopy = () => {
        navigator.clipboard.writeText(knowledgeBase)
        setCopied(true)
        addToast({ type: 'success', message: '已复制到剪贴板' })
        setTimeout(() => setCopied(false), 2000)
    }

    const handleExport = () => {
        const blob = new Blob([knowledgeBase], { type: 'text/plain' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `knowledge_base_${itemId}.txt`
        a.click()
        URL.revokeObjectURL(url)
        addToast({ type: 'success', message: '知识库已导出' })
    }

    const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        const reader = new FileReader()
        reader.onload = (event) => {
            const content = event.target?.result as string
            setKnowledgeBase(content)
            addToast({ type: 'success', message: '知识库已导入' })
        }
        reader.readAsText(file)
        e.target.value = ''
    }

    const getCharWarning = (length: number) => {
        if (length > 10000) return { color: 'text-red-600', message: '⚠️ 超出限制，请精简到10000字以内', bgColor: 'bg-red-50 dark:bg-red-900/20' }
        if (length > 5000) return { color: 'text-yellow-600', message: '⚠️ 内容较长，建议控制在5000字以内', bgColor: 'bg-yellow-50 dark:bg-yellow-900/20' }
        return { color: 'text-green-600', message: '✅ 长度合适', bgColor: 'bg-green-50 dark:bg-green-900/20' }
    }

    const warning = getCharWarning(knowledgeBase.length)

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700">
                    <div className="flex items-center gap-3">
                        <FileText className="w-6 h-6 text-blue-500" />
                        <div>
                            <h2 className="text-lg font-semibold">商品知识库编辑</h2>
                            {itemTitle && <p className="text-sm text-slate-500">{itemTitle}</p>}
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-4">
                    {loading ? (
                        <div className="text-center py-12">
                            <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                            <p className="mt-2 text-slate-500">加载中...</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {/* Toolbar */}
                            <div className="flex flex-wrap gap-2">
                                <button
                                    onClick={() => setShowTemplates(!showTemplates)}
                                    className="btn-ios-secondary text-sm"
                                >
                                    <FileText className="w-4 h-4" />
                                    {showTemplates ? '隐藏模板' : '使用模板'}
                                </button>
                                <button onClick={handleCopy} className="btn-ios-secondary text-sm">
                                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                    复制
                                </button>
                                <button onClick={handleExport} className="btn-ios-secondary text-sm">
                                    <Download className="w-4 h-4" />
                                    导出
                                </button>
                                <label className="btn-ios-secondary text-sm cursor-pointer">
                                    <Upload className="w-4 h-4" />
                                    导入
                                    <input
                                        type="file"
                                        accept=".txt,.md"
                                        className="hidden"
                                        onChange={handleImport}
                                    />
                                </label>
                            </div>

                            {/* Templates */}
                            {showTemplates && (
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    {Object.entries(templates).map(([key, template]) => (
                                        <button
                                            key={key}
                                            onClick={() => handleUseTemplate(key)}
                                            className={`p-3 border rounded-lg text-left transition ${selectedTemplate === key
                                                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                                : 'border-slate-300 dark:border-slate-600 hover:border-blue-300'
                                                }`}
                                        >
                                            <div className="font-medium text-sm">{template.name}</div>
                                            <div className="text-xs text-slate-500 mt-1 line-clamp-2">
                                                {template.content.substring(0, 50)}...
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}

                            {/* Editor */}
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <label className="text-sm font-medium">
                                        知识库内容
                                    </label>
                                    <div className="flex items-center gap-2">
                                        <span className={`text-xs ${warning.color}`}>
                                            {knowledgeBase.length} 字符
                                        </span>
                                        <span className="text-xs text-slate-400">·</span>
                                        <span className={`text-xs ${warning.color}`}>
                                            {warning.message}
                                        </span>
                                    </div>
                                </div>
                                <textarea
                                    value={knowledgeBase}
                                    onChange={(e) => setKnowledgeBase(e.target.value)}
                                    className="w-full h-96 p-4 border border-slate-300 dark:border-slate-600 rounded-lg font-mono text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    placeholder="在此输入商品知识库内容...

提示：
• 使用分段、分点格式，便于AI理解
• 建议长度：2000-5000字（最多10000字）
• AI会基于知识库回答用户问题
• 回复仍受40字限制，AI会自动精简"
                                />
                            </div>

                            {/* Info */}
                            <div className={`${warning.bgColor} border ${warning.color.replace('text-', 'border-').replace('-600', '-200')} rounded-lg p-4`}>
                                <p className="text-sm font-medium mb-2">💡 知识库使用提示</p>
                                <ul className="text-xs space-y-1 list-disc list-inside opacity-90">
                                    <li>AI 会基于知识库内容回答用户问题</li>
                                    <li>建议使用分点、分段的格式，便于 AI 理解</li>
                                    <li>推荐长度：2000-5000字，最多支持10000字</li>
                                    <li>回复仍受40字限制，AI会自动精简回复</li>
                                </ul>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-3 p-4 border-t border-slate-200 dark:border-slate-700">
                    <button onClick={onClose} className="btn-ios-secondary">
                        取消
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving || loading}
                        className="btn-ios-primary"
                    >
                        {saving ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                保存中...
                            </>
                        ) : (
                            <>
                                <Save className="w-4 h-4" />
                                保存
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    )
}
