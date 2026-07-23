/**
 * 消息过滤规则 API
 */
import { get, post, put, del } from '@/utils/request'
import type { ApiResponse } from '@/types'

export interface MessageFilter {
  id: number
  filter_type: 'buyer_id' | 'keyword' | 'item_id'
  filter_value: string
  user_id: number
  enabled: boolean
  description: string | null
  created_at: string
}

export const getMessageFilters = (): Promise<{ filters: MessageFilter[] }> => {
  return get('/message-filters')
}

export const createMessageFilter = (data: {
  filter_type: string
  filter_value: string
  description?: string
}): Promise<{ id: number; msg: string }> => {
  return post('/message-filters', data)
}

export const updateMessageFilter = (
  id: number,
  data: { enabled?: boolean; filter_value?: string },
): Promise<ApiResponse> => {
  return put(`/message-filters/${id}`, data)
}

export const deleteMessageFilter = (id: number): Promise<ApiResponse> => {
  return del(`/message-filters/${id}`)
}
