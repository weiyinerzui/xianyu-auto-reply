import { get, del } from '@/utils/request'
import type { Order, ApiResponse } from '@/types'

// 订单详情类型
export interface OrderDetail extends Order {
  spec_name?: string
  spec_value?: string
}

// 获取订单列表（支持分页）
export const getOrders = async (
  cookieId?: string,
  status?: string,
  page: number = 1,
  pageSize: number = 20
): Promise<{ success: boolean; data: Order[]; total?: number; total_pages?: number }> => {
  const params = new URLSearchParams()
  if (cookieId) params.append('cookie_id', cookieId)
  if (status) params.append('status', status)
  params.append('page', String(page))
  params.append('page_size', String(pageSize))
  const queryString = params.toString()
  
  try {
    const result = await get<{ orders?: Order[]; data?: Order[]; total?: number; total_pages?: number }>(`/api/orders?${queryString}`)
    const orders = result.orders || result.data || []
    return {
      success: true,
      data: orders,
      total: result.total || orders.length,
      total_pages: result.total_pages || Math.ceil((result.total || orders.length) / pageSize)
    }
  } catch {
    return { success: false, data: [], total: 0, total_pages: 0 }
  }
}

// 获取订单详情
export const getOrderDetail = async (orderId: string): Promise<{ success: boolean; data?: OrderDetail }> => {
  try {
    const result = await get<{ order?: OrderDetail; data?: OrderDetail }>(`/api/orders/${orderId}`)
    return {
      success: true,
      data: result.order || result.data
    }
  } catch {
    return { success: false }
  }
}

// 删除订单
export const deleteOrder = async (id: string): Promise<ApiResponse> => {
  try {
    await del(`/api/orders/${id}`)
    return { success: true, message: '删除成功' }
  } catch {
    return { success: false, message: '删除失败' }
  }
}

// 批量删除订单
export const batchDeleteOrders = async (_ids: string[]): Promise<ApiResponse> => {
  return { success: false, message: '后端暂未实现批量删除订单接口' }
}

// 更新订单状态
export const updateOrderStatus = async (_id: string, _status: string): Promise<ApiResponse> => {
  return { success: false, message: '后端暂未实现订单状态更新接口' }
}
