import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'

export type UserRole = 'owner' | 'admin' | 'technician'

export interface AppUser {
    id: string
    full_name: string
    email: string
    role: UserRole
    is_active: boolean
    created_at: string
}

export interface UserCreate {
    full_name: string
    email: string
    password: string
    role: UserRole
}

interface UsersParams {
    page?: number
    page_size?: number
}

export function useUsers(params: UsersParams = {}) {
    return useQuery({
        queryKey: ['users', params],
        queryFn: async () => {
            const { data } = await api.get('/users', { params })
            return data
        },
    })
}

export function useCreateUser() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (payload: UserCreate) => {
            const { data } = await api.post('/users', payload)
            return data as AppUser
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
    })
}

export function useUpdateUserRole() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async ({ id, role }: { id: string; role: UserRole }) => {
            const { data } = await api.patch(`/users/${id}/role`, { role })
            return data as AppUser
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
    })
}

export function useDeleteUser() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: async (id: string) => {
            await api.delete(`/users/${id}`)
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
    })
}