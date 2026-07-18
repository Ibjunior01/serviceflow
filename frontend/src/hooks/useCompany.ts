import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'

export interface Company {
    id: string
    name: string
    slug: string
    document: string | null
    phone: string | null
    email: string | null
    address: string | null
    plan_tier: string
    subscription_status: string | null
    trial_ends_at: string | null
}

export interface CompanyUpdate {
    name?: string
    document?: string
    phone?: string
    email?: string
    address?: string
}

export interface PlanUsage {
    plan_tier: string
    technicians_used: number
    technicians_limit: number | null
    orders_this_month_used: number
    orders_this_month_limit: number | null
    customers_used: number
    customers_limit: number | null
}

export function useCompany() {
    return useQuery({
        queryKey: ['company'],
        queryFn: async () => {
            const { data } = await api.get('/companies/me')
            return data as Company
        },
    })
}

export function usePlanUsage() {
    return useQuery({
        queryKey: ['company', 'usage'],
        queryFn: async () => {
            const { data } = await api.get('/companies/me/usage')
            return data as PlanUsage
        },
    })
}

export function useUpdateCompany() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (payload: CompanyUpdate) => {
            const { data } = await api.patch('/companies/me', payload)
            return data as Company
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ['company'] }),
    })
}