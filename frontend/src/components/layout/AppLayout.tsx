import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function AppLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(false)

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: '#f8fafc' }}>
            <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

            <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
                {/* Barra superior — só aparece em mobile (abaixo de md) */}
                <header
                    className="md:hidden"
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        padding: '14px 16px',
                        background: '#fff',
                        borderBottom: '1px solid #e2e8f0',
                        position: 'sticky',
                        top: 0,
                        zIndex: 30,
                    }}
                >
                    <button
                        onClick={() => setSidebarOpen(true)}
                        aria-label="Abrir menu"
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#0f172a', padding: '4px', display: 'flex', alignItems: 'center' }}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
                        </svg>
                    </button>
                    <span style={{ fontWeight: 600, fontSize: '15px', color: '#0f172a' }}>ServiceFlow</span>
                </header>

                <main className="p-4 md:p-8" style={{ flex: 1, overflow: 'auto' }}>
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
