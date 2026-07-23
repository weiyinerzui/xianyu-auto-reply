/**
 * 自动回复日志 API
 */
import { get } from '@/utils/request'

export interface AutoReplyLog {
  id: number
  cookie_id: string
  user_id: number
  chat_id: string | null
  item_id: string | null
  sender_user_id: string | null
  sender_user_name: string | null
  message_text: string | null
  reply_strategy: string
  matched_keyword: string | null
  reply_text: string | null
  reply_image_url: string | null
  send_status: string
  error_message: string | null
  created_at: string
}

export interface AutoReplyLogStats {
  total: number
  by_strategy: Record<string, number>
  by_status: Record<string, number>
}

export const getAutoReplyLogs = (params: {
  cookie_id?: string
  reply_strategy?: string
  send_status?: string
  limit?: number
  offset?: number
}): Promise<{ logs: AutoReplyLog[] }> => {
  return get('/auto-reply-logs', params)
}

export const getAutoReplyLogStats = (cookieId?: string): Promise<{ stats: AutoReplyLogStats }> => {
  return get('/auto-reply-logs/stats', cookieId ? { cookie_id: cookieId } : {})
}
