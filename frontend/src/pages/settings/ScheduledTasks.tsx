/**
 * 定时任务管理组件
 *
 * 功能：
 * 1. 展示所有定时任务配置（间隔、启用状态、最后执行时间）
 * 2. 编辑执行间隔
 * 3. 开关任务
 * 4. 手动触发执行
 */
import { useState, useEffect, useCallback } from 'react'
import { Clock, Play, Loader2 } from 'lucide-react'

import {
  getScheduledTasks,
  updateScheduledTask,
  triggerScheduledTask,
  type ScheduledTask,
} from '@/api/scheduledTasks'
import { useUIStore } from '@/store/uiStore'

export function ScheduledTasks() {
  const { addToast } = useUIStore()
  const [tasks, setTasks] = useState<ScheduledTask[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<string | null>(null) // task_code being saved
  const [triggering, setTriggering] = useState<string | null>(null) // task_code being triggered

  const fetchTasks = useCallback(async () => {
    try {
      const data = await getScheduledTasks()
      setTasks(data.tasks || [])
    } catch {
      addToast({ type: 'error', message: '获取定时任务列表失败' })
    } finally {
      setLoading(false)
    }
  }, [addToast])

  useEffect(() => {
    void fetchTasks()
  }, [fetchTasks])

  const handleToggle = async (task: ScheduledTask) => {
    setSaving(task.task_code)
    try {
      await updateScheduledTask(task.task_code, { enabled: !task.enabled })
      setTasks((prev) =>
        prev.map((t) =>
          t.task_code === task.task_code ? { ...t, enabled: !t.enabled } : t,
        ),
      )
      addToast({
        type: 'success',
        message: `${task.task_name} 已${!task.enabled ? '启用' : '禁用'}`,
      })
    } catch {
      addToast({ type: 'error', message: '更新失败' })
    } finally {
      setSaving(null)
    }
  }

  const handleIntervalChange = async (task: ScheduledTask, interval: number) => {
    if (interval < 1 || interval === task.interval_seconds) return
    setSaving(task.task_code)
    try {
      await updateScheduledTask(task.task_code, { interval_seconds: interval })
      setTasks((prev) =>
        prev.map((t) =>
          t.task_code === task.task_code ? { ...t, interval_seconds: interval } : t,
        ),
      )
      addToast({ type: 'success', message: `${task.task_name} 间隔已更新` })
    } catch {
      addToast({ type: 'error', message: '更新失败' })
    } finally {
      setSaving(null)
    }
  }

  const handleTrigger = async (task: ScheduledTask) => {
    setTriggering(task.task_code)
    try {
      const result = await triggerScheduledTask(task.task_code)
      addToast({
        type: 'success',
        message: `${task.task_name}: ${result.message || '已触发'}`,
      })
      // 刷新列表以更新 last_run_at
      void fetchTasks()
    } catch {
      addToast({ type: 'error', message: '触发失败' })
    } finally {
      setTriggering(null)
    }
  }

  const formatInterval = (seconds: number) => {
    if (seconds >= 86400) return `${Math.floor(seconds / 86400)} 天`
    if (seconds >= 3600) return `${Math.floor(seconds / 3600)} 小时`
    if (seconds >= 60) return `${Math.floor(seconds / 60)} 分钟`
    return `${seconds} 秒`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-2">
        <Clock className="h-4 w-4 text-slate-500 dark:text-slate-400" />
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          定时任务管理
        </h3>
      </div>

      {tasks.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400 py-4">
          暂无定时任务配置
        </p>
      ) : (
        <div className="space-y-2">
          {tasks.map((task) => (
            <div
              key={task.task_code}
              className="flex items-center justify-between gap-3 py-2.5 px-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700"
            >
              {/* 左侧：任务信息 */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                    {task.task_name}
                  </span>
                  {task.description && (
                    <span className="text-xs text-slate-400 dark:text-slate-500 truncate">
                      {task.description}
                    </span>
                  )}
                </div>
                {task.last_run_at && (
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
                    最后执行: {task.last_run_at}
                  </p>
                )}
              </div>

              {/* 右侧：间隔输入 + 开关 + 触发按钮 */}
              <div className="flex items-center gap-2 shrink-0">
                {/* 间隔输入 */}
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    min={1}
                    value={task.interval_seconds}
                    disabled={saving === task.task_code}
                    onChange={(e) => {
                      const val = parseInt(e.target.value, 10)
                      if (!isNaN(val) && val >= 1) {
                        // 防抖：仅在 blur 或 Enter 时提交
                      }
                    }}
                    onBlur={(e) => {
                      const val = parseInt(e.target.value, 10)
                      if (!isNaN(val) && val >= 1 && val !== task.interval_seconds) {
                        void handleIntervalChange(task, val)
                      }
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        const val = parseInt((e.target as HTMLInputElement).value, 10)
                        if (!isNaN(val) && val >= 1 && val !== task.interval_seconds) {
                          void handleIntervalChange(task, val)
                        }
                      }
                    }}
                    className="w-16 text-center text-sm rounded border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 px-1 py-1 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    title="执行间隔（秒）"
                  />
                  <span className="text-xs text-slate-400 dark:text-slate-500">秒</span>
                </div>

                {/* 开关 */}
                <label className="switch-ios">
                  <input
                    type="checkbox"
                    checked={task.enabled}
                    disabled={saving === task.task_code}
                    onChange={() => void handleToggle(task)}
                  />
                  <span className="switch-slider"></span>
                </label>

                {/* 手动触发 — 仅全局任务可触发 */}
                {(['db_backup', 'delivery_timeout'] as const).includes(task.task_code as 'db_backup' | 'delivery_timeout') ? (
                  <button
                    onClick={() => void handleTrigger(task)}
                    disabled={triggering === task.task_code}
                    title="手动触发"
                    className="p-1.5 rounded-md text-slate-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {triggering === task.task_code ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                  </button>
                ) : (
                  <span title="实例级任务，无法手动触发" className="p-1.5 text-slate-300 dark:text-slate-600">
                    <Play className="h-4 w-4" />
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
