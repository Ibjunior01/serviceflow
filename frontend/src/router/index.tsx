import { lazy, Suspense, type ReactNode } from 'react'
import {
    createBrowserRouter,
    Navigate,
    Outlet,
} from 'react-router-dom'

import AppLayout from '@/components/layout/AppLayout'
import { useAuthStore } from '@/store/authStore'


const LoginPage = lazy(
    () => import('@/pages/LoginPage'),
)

const RegisterPage = lazy(
    () => import('@/pages/RegisterPage'),
)

const DashboardPage = lazy(
    () => import('@/pages/DashboardPage'),
)

const OrdersPage = lazy(
    () => import('@/pages/OrdersPage'),
)

const OrderDetailPage = lazy(
    () => import('@/pages/OrderDetailPage'),
)

const CustomersPage = lazy(
    () => import('@/pages/CustomersPage'),
)

const UsersPage = lazy(
    () => import('@/pages/UsersPage'),
)

const SettingsPage = lazy(
    () => import('@/pages/SettingsPage'),
)


function ProtectedRoute() {
    const token = useAuthStore(
        (state) => state.accessToken,
    )

    return token
        ? <Outlet />
        : <Navigate to="/login" replace />
}


function LazyRoute({
    children,
}: {
    children: ReactNode
}) {
    return (
        <Suspense
            fallback={
                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        minHeight: '200px',
                        color: '#64748b',
                        fontSize: '14px',
                    }}
                >
                    Carregando...
                </div>
            }
        >
            {children}
        </Suspense>
    )
}


export const router = createBrowserRouter([
    {
        path: '/login',
        element: (
            <LazyRoute>
                <LoginPage />
            </LazyRoute>
        ),
    },
    {
        path: '/register',
        element: (
            <LazyRoute>
                <RegisterPage />
            </LazyRoute>
        ),
    },
    {
        element: <ProtectedRoute />,
        children: [
            {
                element: <AppLayout />,
                children: [
                    {
                        path: '/',
                        element: (
                            <LazyRoute>
                                <DashboardPage />
                            </LazyRoute>
                        ),
                    },
                    {
                        path: '/orders',
                        element: (
                            <LazyRoute>
                                <OrdersPage />
                            </LazyRoute>
                        ),
                    },
                    {
                        path: '/orders/:id',
                        element: (
                            <LazyRoute>
                                <OrderDetailPage />
                            </LazyRoute>
                        ),
                    },
                    {
                        path: '/customers',
                        element: (
                            <LazyRoute>
                                <CustomersPage />
                            </LazyRoute>
                        ),
                    },
                    {
                        path: '/users',
                        element: (
                            <LazyRoute>
                                <UsersPage />
                            </LazyRoute>
                        ),
                    },
                    {
                        path: '/settings',
                        element: (
                            <LazyRoute>
                                <SettingsPage />
                            </LazyRoute>
                        ),
                    },
                ],
            },
        ],
    },
])