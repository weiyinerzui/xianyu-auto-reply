/**
 * 卡券-商品关联 API
 */
import { get, post, del } from '@/utils/request'
import type { ApiResponse } from '@/types'

export interface CardItemRelation {
  id: number
  card_id: number
  item_id: string
  user_id: number
  created_at: string
}

// 获取卡券关联的商品列表
export const getCardRelations = (cardId: number): Promise<{ relations: CardItemRelation[] }> => {
  return get(`/cards/${cardId}/relations`)
}

// 添加卡券-商品关联
export const addCardRelation = (cardId: number, itemId: string): Promise<ApiResponse> => {
  return post(`/cards/${cardId}/relations`, { item_id: itemId })
}

// 删除卡券-商品关联
export const removeCardRelation = (cardId: number, itemId: string): Promise<ApiResponse> => {
  return del(`/cards/${cardId}/relations/${itemId}`)
}
