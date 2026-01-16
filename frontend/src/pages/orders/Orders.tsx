import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ShoppingCart, RefreshCw, Search, Trash2, Eye, X, ChevronLeft, ChevronRight } from 'lucide-react'
import { getOrders, deleteOrder, getOrderDetail, type OrderDetail } from '@/api/orders'
import { getAccounts } from '@/api/accounts'
import { useUIStore } from '@/store/uiStore'
import { useAuthStore } from '@/store/authStore'
import { PageLoading } from '@/components/common/Loading'
import { Select } from '@/components/common/Select'
import type { Order, Account } from '@/types'

const statusMap: Record<string, { label: string; class: string }> = {
  processing: { label: '处理中', class: 'badge-warning' },
  pending_ship: { label: '待发货', class: 'badge-info' },
  processed: { label: '已处理', class: 'badge-info' },
  shipped: { label: '已发货', class: 'badge-success' },
  completed: { label: '已完成', class: 'badge-success' },
  refunding: { label: '退款中', class: 'badge-warning' },
  refund_cancelled: { label: '退款撤销', class: 'badge-info' },
  cancelled: { label: '已关闭', class: 'badge-danger' },
  unknown: { label: '未知', class: 'badge-gray' },
}

export function Orders() {
  const { addToast } = useUIStore()
  const { isAuthenticated, token, _hasHydrated } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [orders, setOrders] = useState<Order[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [selectedAccount, setSelectedAccount] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')
  const [searchKeyword, setSearchKeyword] = useState('')
  const [detailModalOpen, setDetailModalOpen] = useState(false)
  const [orderDetail, setOrderDetail] = useState<OrderDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)

  const loadOrders = async (page: number = currentPage) => {
    if (!_hasHydrated || !isAuthenticated || !token) return
    try {
      setLoading(true)
      const result = await getOrders(selectedAccount || undefined, selectedStatus || undefined, page, pageSize)
      if (result.success) {
        setOrders(result.data || [])
        setTotal(result.total || 0)
        setTotalPages(result.total_pages || 0)
        setCurrentPage(page)
      }
    } catch {
      addToast({ type: 'error', message: '加载订单列表失败' })
    } finally {
      setLoading(false)
    }
  }

  const loadAccounts = async () => {
    if (!_hasHydrated || !isAuthenticated || !token) return
    try {
      const data = await getAccounts()
      setAccounts(data)
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    if (!_hasHydrated || !isAuthenticated || !token) return
    loadAccounts()
    loadOrders(1)
  }, [_hasHydrated, isAuthenticated, token])

  useEffect(() => {
    if (!_hasHydrated || !isAuthenticated || !token) return
    setCurrentPage(1)
    loadOrders(1)
  }, [_hasHydrated, isAuthenticated, token, selectedAccount, selectedStatus])

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个订单吗？')) return
    try {
      const result = await deleteOrder(id)
      if (result.success) {
        addToast({ type: 'success', message: '删除成功' })
        loadOrders()
      } else {
        addToast({ type: 'error', message: result.message || '删除失败' })
      }
    } catch {
      addToast({ type: 'error', message: '删除失败' })
    }
  }

  const handleShowDetail = async (orderNo: string) => {
    setLoadingDetail(true)
    setDetailModalOpen(true)
    try {
      const result = await getOrderDetail(orderNo)
      if (result.success && result.data) {
        setOrderDetail(result.data)
      } else {
        addToast({ type: 'error', message: '获取订单详情失败' })
        setDetailModalOpen(false)
      }
    } catch {
      addToast({ type: 'error', message: '获取订单详情失败' })
      setDetailModalOpen(false)
    } finally {
      setLoadingDetail(false)
    }
  }

  const filteredOrders = orders.filter((order) => {
    if (!searchKeyword) return true
    const keyword = searchKeyword.toLowerCase()
    return (
      order.order_id?.toLowerCase().includes(keyword) ||
      order.item_id?.toLowerCase().includes(keyword) ||
      order.buyer_id?.toLowerCase().includes(keyword)
    )
  })

  if (loading && orders.length === 0) {
    return <PageLoading />
  }

  return (
    <div className="space-y-3 sm:space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="page-title">订单管理</h1>
          <p className="page-description">查看和管理所有订单信息</p>
        </div>
        <button onClick={() => loadOrders(currentPage)} className="btn-ios-secondary w-full sm:w-auto">
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="vben-card"
      >
        <div className="vben-card-body">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
            <div className="input-group">
              <label className="input-label">筛选账号</label>
              <Select
                value={selectedAccount}
                onChange={setSelectedAccount}
                options={[
                  { value: '', label: '所有账号' },
                  ...accounts.map((account) => ({
                    value: account.id,
                    label: account.id,
                  })),
                ]}
                placeholder="所有账号"
              />
            </div>
            <div className="input-group">
              <label className="input-label">订单状态</label>
              <Select
                value={selectedStatus}
                onChange={setSelectedStatus}
                options={[
                  { value: '', label: '所有状态' },
                  { value: 'processing', label: '处理中' },
                  { value: 'pending_ship', label: '待发货' },
                  { value: 'shipped', label: '已发货' },
                  { value: 'completed', label: '已完成' },
                  { value: 'refunding', label: '退款中' },
                  { value: 'cancelled', label: '已关闭' },
                ]}
                placeholder="所有状态"
              />
            </div>
            <div className="input-group">
              <label className="input-label">搜索订单</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  placeholder="搜索订单ID或商品ID..."
                  className="input-ios pl-9"
                />
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Orders List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="vben-card"
      >
        <div className="vben-card-header flex items-center justify-between">
          <h2 className="vben-card-title">
            <ShoppingCart className="w-4 h-4" />
            订单列表
          </h2>
          <span className="badge-primary">共 {total} 个订单</span>
        </div>
        <div className="overflow-x-auto">
          <table className="table-ios">
            <thead>
              <tr>
                <th>订单ID</th>
                <th>商品ID</th>
                <th>买家ID</th>
                <th>数量</th>
                <th>金额</th>
                <th>状态</th>
                <th>小刀</th>
                <th>账号ID</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={10} className="text-center py-8 text-gray-500">
                    <div className="flex flex-col items-center gap-2">
                      <ShoppingCart className="w-12 h-12 text-gray-300" />
                      <p>暂无订单数据</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredOrders.map((order) => {
                  const status = statusMap[order.status] || statusMap.unknown
                  return (
                    <tr key={order.id}>
                      <td className="font-mono text-sm">{order.order_id}</td>
                      <td className="text-sm">{order.item_id}</td>
                      <td className="text-sm">{order.buyer_id}</td>
                      <td>{order.quantity}</td>
                      <td className="text-amber-600 font-medium">¥{order.amount}</td>
                      <td>
                        <span className={status.class}>{status.label}</span>
                      </td>
                      <td>
                        {order.is_bargain ? (
                          <span className="badge-warning">是</span>
                        ) : (
                          <span className="badge-gray">否</span>
                        )}
                      </td>
                      <td className="font-medium text-blue-600 dark:text-blue-400">{order.cookie_id}</td>
                      <td className="text-sm text-gray-500">
                        {order.created_at ? new Date(order.created_at).toLocaleString('zh-CN') : '-'}
                      </td>
                      <td>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleShowDetail(order.order_id)}
                            className="p-2 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                            title="查看详情"
                          >
                            <Eye className="w-4 h-4 text-blue-500" />
                          </button>
                          <button
                            onClick={() => handleDelete(order.id)}
                            className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                            title="删除"
                          >
                            <Trash2 className="w-4 h-4 text-red-500" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        {totalPages > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-500">
              第 {currentPage} 页，共 {totalPages} 页，{total} 条记录
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => loadOrders(currentPage - 1)}
                disabled={currentPage <= 1 || loading}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="上一页"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum: number
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => loadOrders(pageNum)}
                      disabled={loading}
                      className={`w-8 h-8 rounded-lg text-sm transition-colors ${
                        currentPage === pageNum
                          ? 'bg-blue-500 text-white'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                      }`}
                    >
                      {pageNum}
                    </button>
                  )
                })}
              </div>
              <button
                onClick={() => loadOrders(currentPage + 1)}
                disabled={currentPage >= totalPages || loading}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                title="下一页"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </motion.div>

      {/* 订单详情弹窗 */}
      {detailModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content max-w-2xl">
            <div className="modal-header flex items-center justify-between">
              <h2 className="text-lg font-semibold">订单详情</h2>
              <button
                onClick={() => setDetailModalOpen(false)}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <div className="modal-body">
              {loadingDetail ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  <span className="ml-2 text-gray-500">加载中...</span>
                </div>
              ) : orderDetail ? (
                <div className="space-y-4">
                  {/* 基本信息 */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">基本信息</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">订单ID</span>
                        <span className="font-mono">{orderDetail.order_id}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">商品ID</span>
                        <span>{orderDetail.item_id || '未知'}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">买家ID</span>
                        <span>{orderDetail.buyer_id || '未知'}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">账号ID</span>
                        <span className="text-blue-600">{orderDetail.cookie_id || '未知'}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">订单状态</span>
                        <span className={statusMap[orderDetail.status]?.class || 'badge-gray'}>
                          {statusMap[orderDetail.status]?.label || '未知'}
                        </span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">是否小刀</span>
                        {orderDetail.is_bargain ? (
                          <span className="badge-warning">是</span>
                        ) : (
                          <span className="badge-gray">否</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* 商品信息 */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">商品信息</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">规格名称</span>
                        <span>{orderDetail.spec_name || '无'}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">规格值</span>
                        <span>{orderDetail.spec_value || '无'}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">数量</span>
                        <span>{orderDetail.quantity || 1}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">金额</span>
                        <span className="text-amber-600 font-medium">¥{orderDetail.amount || '0.00'}</span>
                      </div>
                    </div>
                  </div>

                  {/* 时间信息 */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">时间信息</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">创建时间</span>
                        <span>{orderDetail.created_at ? new Date(orderDetail.created_at).toLocaleString('zh-CN') : '未知'}</span>
                      </div>
                      <div className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-700">
                        <span className="text-gray-500">更新时间</span>
                        <span>{orderDetail.updated_at ? new Date(orderDetail.updated_at).toLocaleString('zh-CN') : '未知'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">暂无数据</div>
              )}
            </div>
            <div className="modal-footer">
              <button onClick={() => setDetailModalOpen(false)} className="btn-ios-secondary">
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
