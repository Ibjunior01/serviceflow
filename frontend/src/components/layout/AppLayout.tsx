import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function AppLayout() {
    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: '#f8fafc' }}>
            <Sidebar />
            <main style={{ flex: 1, overflow: 'auto', padding: '32px' }}>
                <Outlet />
            </main>
        </div>
    )
}