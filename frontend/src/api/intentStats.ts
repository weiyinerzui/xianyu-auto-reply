/**
 * 意图识别统计 API
 */
import { get } from '@/utils/request'

export interface IntentStats {
  total: number
  by_strategy: Record<string, number>
  by_status: Record<string, number>
  daily_trend: Record<string, Record<string, number>>
  days: number
}

export const getIntentStats = (
  cookieId?: string,
  days?: number,
): Promise<{ stats: IntentStats }> => {
  const params: Record<string, string | number> = {}
  if (cookieId) params.cookie_id = cookieId
  if (days) params.days = days
  return get('/intent-stats', params)
}
