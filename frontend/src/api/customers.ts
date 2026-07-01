import { api } from './client'

export interface Customer {
    id: string
    name: string
    email: string | null
    phone: string | null
}

export interface PaginatedCustomers {
    items: Customer[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export const customersApi = {
    list: (params?: { page?: number; page_size?: number; search?: string }) =>
        api.get<PaginatedCustomers>('/customers', { params }),
}