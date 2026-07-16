import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { ordersApi } from '@/api/orders'
import type { ServiceOrder } from '@/api/orders'

const STATUS_LABEL: Record<string, string> = {
    draft: 'Rascunho',
    scheduled: 'Agendada',
    in_progress: 'Em andamento',
    completed: 'Concluída',
    invoiced: 'Faturada',
    cancelled: 'Cancelada',
}

const STATUS_COLOR: Record<string, { bg: string; text: string }> = {
    draft: { bg: '#f1f5f9', text: '#475569' },
    scheduled: { bg: '#f0f9ff', text: '#0369a1' },
    in_progress: { bg: '#fff7ed', text: '#c2410c' },
    completed: { bg: '#f0fdf4', text: '#15803d' },
    invoiced: { bg: '#faf5ff', text: '#7e22ce' },
    cancelled: { bg: '#fef2f2', text: '#dc2626' },
}

const PRIORITY_COLOR: Record<ServiceOrder['priority'], string> = {
    low: '#22c55e',
    normal: '#f59e0b',
    high: '#ef4444',
    urgent: '#7c3aed',
}

const PRIORITY_LABEL: Record<ServiceOrder['priority'], string> = {
    low: 'Baixa',
    normal: 'Média',
    high: 'Alta',
    urgent: 'Urgente',
}

const STAT_STATUSES: Array<{ key: ServiceOrder['status']; label: string; icon: string }> = [
    { key: 'in_progress', label: 'Em andamento', icon: '🔧' },
    { key: 'completed', label: 'Concluídas', icon: '✅' },
    { key: 'invoiced', label: 'Faturadas', icon: '💰' },
]

export default function DashboardPage() {
    const navigate = useNavigate()
    const user = useAuthStore((s) => s.user)

    const { data, isLoading } = useQuery({
        queryKey: ['orders', 'dashboard'],
        queryFn: () => ordersApi.list({ page: 1, page_size: 50 }),
    })

    const orders = data?.data.items ?? []

    const countByStatus = (status: ServiceOrder['status']) =>
        orders.filter((o) => o.status === status).length

    const recent = orders.slice(0, 8)

    const hour = new Date().getHours()
    const greeting = hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite'
    const firstName = user?.full_name?.split(' ')[0] ?? ''

    return (
        <div style={{ maxWidth: '960px' }}>
            {/* Header */}
            <div style={{ marginBottom: '32px' }}>
                <h1 style={{ fontSize: '22px', fontWeight: 600, color: '#0f172a', margin: '0 0 4px', letterSpacing: '-0.025em' }}>
                    {greeting}, {firstName}
                </h1>
                <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>
                    Aqui está o resumo das ordens de serviço.
                </p>
            </div>

            {/* Stat cards — 2 colunas em mobile, 4 a partir de sm (640px) */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
                {STAT_STATUSES.map((s) => (
                    <div
                        key={s.key}
                        onClick={() => navigate(`/orders?status=${s.key}`)}
                        style={{
                            background: '#fff',
                            border: '1px solid #e2e8f0',
                            borderRadius: '12px',
                            padding: '20px',
                            cursor: 'pointer',
                            transition: 'border-color 0.15s',
                        }}
                        onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.borderColor = '#3b82f6' }}
                        onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.borderColor = '#e2e8f0' }}
                    >
                        <p style={{ fontSize: '22px', margin: '0 0 8px' }}>{s.icon}</p>
                        {isLoading ? (
                            <div style={{ height: '28px', width: '40px', background: '#f1f5f9', borderRadius: '6px', marginBottom: '6px' }} />
                        ) : (
                            <p style={{ fontSize: '28px', fontWeight: 600, color: '#0f172a', margin: '0 0 4px', letterSpacing: '-0.03em' }}>
                                {countByStatus(s.key)}
                            </p>
                        )}
                        <p style={{ fontSize: '13px', color: '#64748b', margin: 0 }}>{s.label}</p>
                    </div>
                ))}
            </div>

            {/* Recent orders */}
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#0f172a', margin: 0 }}>
                        Ordens recentes
                    </h2>
                    <button
                        onClick={() => navigate('/orders')}
                        style={{ fontSize: '13px', color: '#3b82f6', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}
                    >
                        Ver todas →
                    </button>
                </div>

                {isLoading ? (
                    <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8', fontSize: '14px' }}>
                        Carregando…
                    </div>
                ) : recent.length === 0 ? (
                    <div style={{ padding: '48px', textAlign: 'center' }}>
                        <p style={{ fontSize: '14px', color: '#94a3b8', margin: '0 0 12px' }}>Nenhuma ordem cadastrada ainda.</p>
                        <button
                            onClick={() => navigate('/orders')}
                            style={{ fontSize: '13px', color: '#3b82f6', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}
                        >
                            Criar primeira OS →
                        </button>
                    </div>
                ) : (
                    // Wrapper com scroll horizontal contido — a tabela pode rolar dentro do
                    // card sem nunca empurrar a largura da página inteira (o que causava o
                    // "scroll pra ver o último indicador" reportado).
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8fafc' }}>
                                    {['Nº', 'Título', 'Cliente', 'Prioridade', 'Status', 'Data'].map((h) => (
                                        <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: '12px', fontWeight: 500, color: '#94a3b8', whiteSpace: 'nowrap' }}>
                                            {h}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {recent.map((order, i) => (
                                    <tr
                                        key={order.id}
                                        onClick={() => navigate(`/orders/${order.id}`)}
                                        style={{
                                            borderTop: i > 0 ? '1px solid #f1f5f9' : 'none',
                                            cursor: 'pointer',
                                            transition: 'background 0.1s',
                                        }}
                                        onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = '#f8fafc' }}
                                        onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = 'transparent' }}
                                    >
                                        <td style={{ padding: '12px 16px', fontSize: '13px', color: '#64748b', fontWeight: 500, whiteSpace: 'nowrap' }}>
                                            #{order.order_number}
                                        </td>
                                        <td style={{ padding: '12px 16px', fontSize: '13px', color: '#0f172a', maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {order.title}
                                        </td>
                                        <td style={{ padding: '12px 16px', fontSize: '13px', color: '#64748b', maxWidth: '160px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {order.customer_name ?? '—'}
                                        </td>
                                        <td style={{ padding: '12px 16px' }}>
                                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: PRIORITY_COLOR[order.priority], fontWeight: 500, whiteSpace: 'nowrap' }}>
                                                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: PRIORITY_COLOR[order.priority], flexShrink: 0 }} />
                                                {PRIORITY_LABEL[order.priority]}
                                            </span>
                                        </td>
                                        <td style={{ padding: '12px 16px' }}>
                                            <span style={{
                                                display: 'inline-block',
                                                padding: '3px 8px',
                                                borderRadius: '6px',
                                                fontSize: '12px',
                                                fontWeight: 500,
                                                whiteSpace: 'nowrap',
                                                background: (STATUS_COLOR[order.status] ?? STATUS_COLOR['draft']).bg,
                                                color: (STATUS_COLOR[order.status] ?? STATUS_COLOR['draft']).text,
                                            }}>
                                                {STATUS_LABEL[order.status]}
                                            </span>
                                        </td>
                                        <td style={{ padding: '12px 16px', fontSize: '12px', color: '#94a3b8', whiteSpace: 'nowrap' }}>
                                            {new Date(order.created_at).toLocaleDateString('pt-BR')}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
