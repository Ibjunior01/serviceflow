import { api } from './client'
import type { ServiceOrder } from './orders'


export interface DashboardStatusCounts {
    draft: number
    scheduled: number
    in_progress: number
    completed: number
    invoiced: number
    cancelled: number
}


export interface DashboardMonthlyPoint {
    year: number
    month: number
    count: number
}


export interface DashboardSummary {
    status_counts: DashboardStatusCounts
    monthly_orders: DashboardMonthlyPoint[]
    recent_orders: ServiceOrder[]
}


export const dashboardApi = {
    getSummary: () =>
        api.get<DashboardSummary>('/dashboard/summary'),
}