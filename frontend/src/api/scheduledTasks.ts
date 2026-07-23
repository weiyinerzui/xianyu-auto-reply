/**
 * 定时任务管理 API
 */
import { get, put, post } from '@/utils/request'
import type { ApiResponse } from '@/types'

export interface ScheduledTask {
  id: number
  task_code: string
  task_name: string
  interval_seconds: number
  enabled: boolean
  description: string | null
  last_run_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface ScheduledTaskUpdate {
  interval_seconds?: number
  enabled?: boolean
}

// 获取所有定时任务
export const getScheduledTasks = (): Promise<{ tasks: ScheduledTask[] }> => {
  return get('/scheduled-tasks')
}

// 更新定时任务配置
export const updateScheduledTask = (
  taskCode: string,
  data: ScheduledTaskUpdate,
): Promise<ApiResponse> => {
  return put(`/scheduled-tasks/${taskCode}`, data)
}

// 手动触发定时任务
export const triggerScheduledTask = (
  taskCode: string,
): Promise<ApiResponse> => {
  return post(`/scheduled-tasks/${taskCode}/trigger`)
}
