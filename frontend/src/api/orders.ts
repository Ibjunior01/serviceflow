import { api } from './client'

export interface ServiceOrder {
    id: string
    order_number: string
    title: string
    status: 'draft' | 'scheduled' | 'assigned' | 'in_progress' | 'completed' | 'invoiced' | 'cancelled'
    priority: 'low' | 'normal' | 'high' | 'urgent'
    customer_name?: string
    technician_name?: string
    created_at: string
    scheduled_at?: string
}

export interface ServiceOrderDetail {
    id: string
    order_number: string
    title: string
    description?: string
    status: 'draft' | 'scheduled' | 'assigned' | 'in_progress' | 'completed' | 'invoiced' | 'cancelled'
    priority: 'low' | 'normal' | 'high' | 'urgent'
    customer_id?: string
    customer_name?: string
    technician_id?: string
    technician_name?: string
    scheduled_at?: string
    started_at?: string
    completed_at?: string
    total_amount?: number
    created_at: string
    updated_at: string
}

export interface OrderItem {
    id: string
    description: string
    quantity: number
    unit_price: number
    total_price: number
}

export interface PaginatedOrders {
    items: ServiceOrder[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

// ✅ NOVO — payload de criação alinhado com o backend
export interface ServiceOrderCreate {
    title: string
    description?: string
    priority: 'low' | 'normal' | 'high' | 'urgent'
    customer_id?: string
    assigned_to?: string        // backend usa assigned_to → technician_id
    scheduled_at?: string       // ISO string ou undefined
}

export interface ServiceOrderUpdate {
    title?: string
    description?: string
    priority?: 'low' | 'normal' | 'high' | 'urgent'
    customer_id?: string
    assigned_to?: string
    scheduled_at?: string
}

export const ordersApi = {
    list: (params?: { page?: number; page_size?: number; status?: string }) =>
        api.get<PaginatedOrders>('/orders', { params }),

    getById: (id: string) =>
        api.get<ServiceOrderDetail>(`/orders/${id}`),

    // ✅ NOVO
    create: (payload: ServiceOrderCreate) =>
        api.post<ServiceOrderDetail>('/orders', payload),

    // ✅ NOVO
    update: (id: string, payload: ServiceOrderUpdate) =>
        api.patch<ServiceOrderDetail>(`/orders/${id}`, payload),

    updateStatus: (id: string, status: ServiceOrderDetail['status']) =>
        api.patch(`/orders/${id}/status`, { status }),

    getItems: (id: string) =>
        api.get<OrderItem[]>(`/orders/${id}/items`),

    delete: (id: string) =>
        api.delete(`/orders/${id}`),
}