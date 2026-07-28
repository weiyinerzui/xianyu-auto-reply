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
  // 后端批量查询附带的商品信息（可能为 null）
  item_title?: string | null
  item_price?: string | null
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

// ==================== 卡券关联商品搜索 ====================

// 搜索可关联商品轻量项
export interface SearchItemForCard {
  item_id: string
  item_title: string
  item_price: string
}

// 搜索当前用户账号下的商品（按ID或标题模糊匹配）
export const searchItemsForCard = async (
  keyword: string,
): Promise<{ success: boolean; items: SearchItemForCard[] }> => {
  const params = new URLSearchParams()
  if (keyword.trim()) {
    params.set('keyword', keyword.trim())
  }
  const qs = params.toString()
  const result = await get<{ items: SearchItemForCard[]; total: number }>(
    `/cards/search-items${qs ? `?${qs}` : ''}`,
  )
  return {
    success: true,
    items: result.items || [],
  }
}
