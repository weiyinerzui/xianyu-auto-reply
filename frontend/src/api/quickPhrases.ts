/**
 * 快捷短语 API
 */
import { get, post, put, del } from '@/utils/request'
import type { ApiResponse } from '@/types'

export interface QuickPhrase {
  id: number
  title: string
  content: string
  sort_order: number
  user_id: number
  created_at: string
}

export const getQuickPhrases = (): Promise<{ phrases: QuickPhrase[] }> => {
  return get('/quick-phrases')
}

export const createQuickPhrase = (data: {
  title: string
  content: string
  sort_order?: number
}): Promise<{ id: number; msg: string }> => {
  return post('/quick-phrases', data)
}

export const updateQuickPhrase = (
  id: number,
  data: { title: string; content: string; sort_order: number },
): Promise<ApiResponse> => {
  return put(`/quick-phrases/${id}`, data)
}

export const deleteQuickPhrase = (id: number): Promise<ApiResponse> => {
  return del(`/quick-phrases/${id}`)
}
