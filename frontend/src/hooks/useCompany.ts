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
    subscription_plan: string
    subscription_status: string
    trial_ends_at: string | null
}

export interface CompanyUpdate {
    name?: string
    document?: string
    phone?: string
    email?: string
    address?: string
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