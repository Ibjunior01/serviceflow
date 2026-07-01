import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import AppLayout from '@/components/layout/AppLayout'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import OrdersPage from '@/pages/OrdersPage'
import OrderDetailPage from '@/pages/OrderDetailPage'
import CustomersPage from '@/pages/CustomersPage'
import UsersPage from '@/pages/UsersPage'
import SettingsPage from '@/pages/SettingsPage'

function ProtectedRoute() {
    const token = useAuthStore((s) => s.accessToken)
    return token ? <Outlet /> : <Navigate to="/login" replace />
}

export const router = createBrowserRouter([
    { path: '/login', element: <LoginPage /> },
    {
        element: <ProtectedRoute />,
        children: [
            {
                element: <AppLayout />,
                children: [
                    { path: '/', element: <DashboardPage /> },
                    { path: '/orders', element: <OrdersPage /> },
                    { path: '/orders/:id', element: <OrderDetailPage /> },
                    { path: '/customers', element: <CustomersPage /> },
                    { path: '/users', element: <UsersPage /> },
                    { path: '/settings', element: <SettingsPage /> },
                ],
            },
        ],
    },
])