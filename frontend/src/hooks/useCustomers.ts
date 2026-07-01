import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'

export interface Customer {
    id: string
    name: string
    email: string | null
    phone: string | null
    document: string | null
    address_street: string | null
    address_number: string | null
    address_complement: string | null
    address_neighborhood: string | null
    address_city: string | null
    address_state: string | null
    address_zip: string | null
    created_at: string
}

export interface CustomerCreate {
    name: string
    email?: string
    phone?: string
    document?: string
    address_street?: string
    address_number?: string
    address_complement?: string
    address_neighborhood?: string
    address_city?: string
    address_state?: string
    address_zip?: string
}

interface CustomersParams {
    page?: number
    page_size?: number
    search?: string
}

export function useCustomers(params: CustomersParams = {}) {
    return useQuery({
        queryKey: ['customers', params],
        queryFn: async () => {
            const { data } = await api.get('/customers', { params })
            return data // PaginatedResponse<Customer>
        },
    })
}

export function useCustomer(id: string) {
    return useQuery({
        queryKey: ['customers', id],
        queryFn: async () => {
            const { data } = await api.get(`/customers/${id}`)
            return data as Customer
        },
        enabled: !!id,
    })
}

export function useCreateCustomer() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (payload: CustomerCreate) => {
            const { data } = await api.post('/customers', payload)
            return data as Customer
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ['customers'] }),
    })
}

export function useUpdateCustomer() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async ({ id, payload }: { id: string; payload: Partial<CustomerCreate> }) => {
            const { data } = await api.patch(`/customers/${id}`, payload)
            return data as Customer
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ['customers'] }),
    })
}

export function useDeleteCustomer() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (id: string) => {
            await api.delete(`/customers/${id}`)
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ['customers'] }),
    })
}