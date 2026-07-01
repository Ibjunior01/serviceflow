import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ordersApi, type ServiceOrderCreate, type ServiceOrderUpdate } from '@/api/orders'

// ─── Listagem paginada ────────────────────────────────────────────────────────
interface OrdersParams {
    page?: number
    page_size?: number
    status?: string
}

export function useOrders(params: OrdersParams = {}) {
    return useQuery({
        queryKey: ['orders', params],
        queryFn: async () => {
            const { data } = await ordersApi.list(params)
            return data
        },
    })
}

// ─── Detalhe de uma OS ────────────────────────────────────────────────────────
export function useOrder(id: string) {
    return useQuery({
        queryKey: ['orders', id],
        queryFn: async () => {
            const { data } = await ordersApi.getById(id)
            return data
        },
        enabled: !!id,
    })
}

// ─── Criação ──────────────────────────────────────────────────────────────────
export function useCreateOrder() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (payload: ServiceOrderCreate) => {
            const { data } = await ordersApi.create(payload)
            return data
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ['orders'] }),
    })
}

// ─── Atualização ──────────────────────────────────────────────────────────────
export function useUpdateOrder(id: string) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (payload: ServiceOrderUpdate) => {
            const { data } = await ordersApi.update(id, payload)
            return data
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['orders'] })
            qc.invalidateQueries({ queryKey: ['orders', id] })
        },
    })
}

// ─── Exclusão ─────────────────────────────────────────────────────────────────
export function useDeleteOrder() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (id: string) => {
            await ordersApi.delete(id)
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ['orders'] }),
    })
}

// ─── Transição de status ──────────────────────────────────────────────────────
export function useUpdateOrderStatus(id: string) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (status: string) => {
            const { data } = await ordersApi.updateStatus(id, status as any)
            return data
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['orders'] })
            qc.invalidateQueries({ queryKey: ['orders', id] })
        },
    })
}