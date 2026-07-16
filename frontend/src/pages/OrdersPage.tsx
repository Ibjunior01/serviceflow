import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { useQuery } from '@tanstack/react-query'
import { ordersApi, type ServiceOrder } from '@/api/orders'
import { useCreateOrder } from '@/hooks/useOrders'
import { api } from '@/api/client'
import { useAuthStore } from '@/store/authStore'
import { Skeleton } from '@/components/ui/skeleton'
import { formatOrderNumber } from '@/lib/format'

// ─── Schema de validação ──────────────────────────────────────────────────────
const createOrderSchema = z.object({
    title: z.string().min(3, 'Título deve ter pelo menos 3 caracteres'),
    description: z.string().optional(),
    priority: z.enum(['low', 'normal', 'high', 'urgent']),
    customer_id: z.string().optional(),
    scheduled_at: z.string().optional(),
})

type CreateOrderForm = z.infer<typeof createOrderSchema>

// ─── Constantes de UI ─────────────────────────────────────────────────────────
const STATUS_LABEL: Record<string, string> = {
    draft: 'Rascunho', scheduled: 'Agendada',
    in_progress: 'Em andamento', completed: 'Concluída',
    invoiced: 'Faturada', cancelled: 'Cancelada',
}

const STATUS_COLOR: Record<string, { bg: string; text: string }> = {
    draft: { bg: '#f1f5f9', text: '#475569' },
    scheduled: { bg: '#f0f9ff', text: '#0369a1' },
    in_progress: { bg: '#fff7ed', text: '#c2410c' },
    completed: { bg: '#f0fdf4', text: '#15803d' },
    invoiced: { bg: '#faf5ff', text: '#7e22ce' },
    cancelled: { bg: '#fef2f2', text: '#dc2626' },
}

const PRIORITY_COLOR: Record<string, string> = {
    low: '#22c55e', normal: '#f59e0b', high: '#ef4444', urgent: '#7c3aed',
}

const PRIORITY_LABEL: Record<string, string> = {
    low: 'Baixa', normal: 'Média', high: 'Alta', urgent: 'Urgente',
}

const STATUS_FILTERS = [
    { value: '', label: 'Todas' },
    { value: 'draft', label: 'Rascunho' },
    { value: 'scheduled', label: 'Agendada' },
    { value: 'in_progress', label: 'Em andamento' },
    { value: 'completed', label: 'Concluída' },
    { value: 'invoiced', label: 'Faturada' },
    { value: 'cancelled', label: 'Cancelada' },
]

// ─── Estilos de campo reutilizáveis ──────────────────────────────────────────
const fieldStyle: React.CSSProperties = {
    width: '100%', padding: '8px 10px', borderRadius: '7px',
    border: '1px solid #e2e8f0', fontSize: '13px', color: '#0f172a',
    outline: 'none', background: '#fff', boxSizing: 'border-box',
    colorScheme: 'light',
}

const labelStyle: React.CSSProperties = {
    display: 'block', fontSize: '12px', fontWeight: 500,
    color: '#475569', marginBottom: '5px',
}

const errorStyle: React.CSSProperties = {
    fontSize: '11px', color: '#ef4444', marginTop: '3px',
}

// ─── Dropdown customizado (Chrome ignora style em <option>) ───────────────────
function CustomSelect({
    options,
    value,
    onChange,
    placeholder,
    loading,
}: {
    options: { id: string; name: string }[]
    value: string
    onChange: (v: string) => void
    placeholder: string
    loading?: boolean
}) {
    const [open, setOpen] = useState(false)
    const selected = options.find((o) => o.id === value)

    return (
        <div style={{ position: 'relative' }}>
            <button
                type="button"
                onClick={() => setOpen((p) => !p)}
                style={{
                    ...fieldStyle, textAlign: 'left', cursor: 'pointer',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}
            >
                <span style={{ color: selected ? '#0f172a' : '#94a3b8' }}>
                    {loading ? '— Carregando… —' : (selected?.name ?? placeholder)}
                </span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
                    <polyline points="6 9 12 15 18 9" />
                </svg>
            </button>

            {open && (
                <div style={{
                    position: 'absolute', bottom: 'calc(100% + 4px)', left: 0, right: 0,
                    background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.12)', zIndex: 50,
                    maxHeight: '200px', overflowY: 'auto',
                }}>
                    <div
                        onClick={() => { onChange(''); setOpen(false) }}
                        style={{
                            padding: '8px 12px', fontSize: '13px', color: '#94a3b8',
                            cursor: 'pointer', borderBottom: '1px solid #f1f5f9',
                        }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
                        onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                    >
                        — Sem técnico atribuído —
                    </div>
                    {options.map((o) => (
                        <div
                            key={o.id}
                            onClick={() => { onChange(o.id); setOpen(false) }}
                            style={{
                                padding: '8px 12px', fontSize: '13px', color: '#0f172a',
                                cursor: 'pointer',
                                background: value === o.id ? '#eff6ff' : 'transparent',
                                fontWeight: value === o.id ? 500 : 400,
                            }}
                            onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
                            onMouseLeave={(e) => (e.currentTarget.style.background = value === o.id ? '#eff6ff' : 'transparent')}
                        >
                            {o.name}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}


// ─── Componente Modal ─────────────────────────────────────────────────────────
function CreateOrderModal({ onClose }: { onClose: () => void }) {
    const createOrder = useCreateOrder()
    const user = useAuthStore((s) => s.user)
    const canAssign = ['admin', 'owner'].includes(user?.role ?? '')
    // Adicionar junto aos outros states do modal
    const [assignedTo, setAssignedTo] = useState('')

    // Query de clientes
    const { data: customersData } = useQuery({
        queryKey: ['customers-select'],
        queryFn: async () => {
            const { data } = await api.get('/customers', { params: { page: 1, page_size: 100 } })
            return data
        },
        staleTime: 60_000,
    })

    // Query de usuários — só dispara para admin/owner
    const { data: usersData, isLoading: loadingUsers } = useQuery({
        queryKey: ['users-select'],
        queryFn: async () => {
            const { data } = await api.get('/users', { params: { page: 1, page_size: 100 } })
            return data
        },
        enabled: canAssign,
        retry: false,
        staleTime: 60_000,
    })

    const customers = customersData?.items ?? []
    const technicians = canAssign
        ? (usersData?.items ?? []).filter(
            (u: any) => ['technician', 'admin', 'owner'].includes(u.role)
        )
        : []

    const {
        register,
        handleSubmit,
        formState: { errors, isSubmitting },
    } = useForm<CreateOrderForm>({
        resolver: zodResolver(createOrderSchema),
        defaultValues: { priority: 'normal' },
    })

    const onSubmit = async (values: CreateOrderForm) => {
        try {
            const payload = {
                ...values,
                customer_id: values.customer_id || undefined,
                technician_id: assignedTo || undefined,
                scheduled_at: values.scheduled_at
                    ? new Date(values.scheduled_at).toISOString()
                    : undefined,
            }
            await createOrder.mutateAsync(payload)
            toast.success('Ordem de serviço criada com sucesso!')
            onClose()
        } catch (err: any) {
            const detail = err?.response?.data?.detail
            let msg = 'Erro ao criar ordem de serviço'
            if (typeof detail === 'string') {
                msg = detail
            } else if (Array.isArray(detail)) {
                msg = detail.map((e: any) => `${e.loc?.at(-1)}: ${e.msg}`).join(' | ')
            }
            toast.error(msg)
        }
    }

    return (
        <div
            onClick={onClose}
            style={{
                position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                zIndex: 1000, padding: '16px',
            }}
        >
            <div
                onClick={(e) => e.stopPropagation()}
                style={{
                    background: '#fff', borderRadius: '14px', width: '100%', maxWidth: '520px',
                    maxHeight: 'calc(100vh - 32px)', overflowY: 'auto',
                    boxShadow: '0 20px 60px rgba(0,0,0,0.18)',
                }}
            >
                <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h2 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#0f172a' }}>
                            Nova Ordem de Serviço
                        </h2>
                        <p style={{ margin: '2px 0 0', fontSize: '13px', color: '#94a3b8' }}>
                            Preencha os dados da OS
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '4px', lineHeight: 1 }}
                    >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} style={{ padding: '20px 24px 24px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

                        <div>
                            <label style={labelStyle}>Título *</label>
                            <input
                                {...register('title')}
                                placeholder="Ex: Instalação de ar-condicionado"
                                style={{ ...fieldStyle, borderColor: errors.title ? '#ef4444' : '#e2e8f0' }}
                            />
                            {errors.title && <p style={errorStyle}>{errors.title.message}</p>}
                        </div>

                        <div>
                            <label style={labelStyle}>Descrição</label>
                            <textarea
                                {...register('description')}
                                placeholder="Detalhes adicionais sobre o serviço…"
                                rows={3}
                                style={{ ...fieldStyle, resize: 'vertical', fontFamily: 'inherit' }}
                            />
                        </div>

                        {/* Prioridade + Agendamento — 1 coluna em mobile, 2 a partir de sm (640px) */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                                <label style={labelStyle}>Prioridade *</label>
                                <select {...register('priority')} style={fieldStyle}>
                                    <option value="low">Baixa</option>
                                    <option value="normal">Média</option>
                                    <option value="high">Alta</option>
                                    <option value="urgent">Urgente</option>
                                </select>
                            </div>
                            <div>
                                <label style={labelStyle}>Agendamento</label>
                                <input
                                    type="datetime-local"
                                    {...register('scheduled_at')}
                                    style={fieldStyle}
                                />
                            </div>
                        </div>

                        <div>
                            <label style={labelStyle}>Cliente</label>
                            <select {...register('customer_id')} style={fieldStyle}>
                                <option value="">— Selecione um cliente —</option>
                                {customers.map((c: any) => (
                                    <option key={c.id} value={c.id}>{c.name}</option>
                                ))}
                            </select>
                        </div>

                        {canAssign && (
                            <div>
                                <label style={labelStyle}>Técnico responsável</label>
                                <CustomSelect
                                    options={technicians.map((u: any) => ({ id: u.id, name: u.full_name }))}
                                    value={assignedTo}
                                    onChange={setAssignedTo}
                                    placeholder="— Sem técnico atribuído —"
                                    loading={loadingUsers}
                                />
                            </div>
                        )}

                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '24px' }}>
                        <button
                            type="button"
                            onClick={onClose}
                            style={{
                                padding: '8px 16px', borderRadius: '8px', border: '1px solid #e2e8f0',
                                background: '#fff', fontSize: '13px', color: '#475569', cursor: 'pointer', fontWeight: 500,
                            }}
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            style={{
                                padding: '8px 20px', borderRadius: '8px', border: 'none',
                                background: isSubmitting ? '#93c5fd' : '#3b82f6',
                                color: '#fff', fontSize: '13px', fontWeight: 500,
                                cursor: isSubmitting ? 'not-allowed' : 'pointer',
                                transition: 'background 0.15s',
                            }}
                        >
                            {isSubmitting ? 'Criando…' : 'Criar OS'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

// ─── Página principal ─────────────────────────────────────────────────────────
export default function OrdersPage() {
    const navigate = useNavigate()
    const [statusFilter, setStatusFilter] = useState('')
    const [page, setPage] = useState(1)
    const [showCreateModal, setShowCreateModal] = useState(false)

    const { data, isLoading } = useQuery({
        queryKey: ['orders', page, statusFilter],
        queryFn: () => ordersApi.list({ page, page_size: 20, status: statusFilter || undefined }),
    })

    const orders = data?.data.items ?? []
    const totalPages = data?.data.total_pages ?? 1
    const total = data?.data.total ?? 0


    return (
        <div style={{ maxWidth: '1100px' }}>
            {showCreateModal && (
                <CreateOrderModal onClose={() => setShowCreateModal(false)} />
            )}

            {/* Header — flexWrap evita que o botão "Nova OS" espreme o título em telas estreitas */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                    <h1 style={{ fontSize: '22px', fontWeight: 600, color: '#0f172a', margin: '0 0 4px', letterSpacing: '-0.025em' }}>
                        Ordens de Serviço
                    </h1>
                    <p style={{ fontSize: '14px', color: '#64748b', margin: 0 }}>
                        {isLoading ? '…' : `${total} ordem${total !== 1 ? 's' : ''} encontrada${total !== 1 ? 's' : ''}`}
                    </p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    style={{
                        display: 'flex', alignItems: 'center', gap: '6px',
                        padding: '8px 16px', borderRadius: '8px',
                        background: '#3b82f6', color: '#fff',
                        border: 'none', fontSize: '14px', fontWeight: 500, cursor: 'pointer',
                    }}
                >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    Nova OS
                </button>
            </div>

            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '20px' }}>
                {STATUS_FILTERS.map((f) => (
                    <button
                        key={f.value}
                        onClick={() => { setStatusFilter(f.value); setPage(1) }}
                        style={{
                            padding: '5px 12px', borderRadius: '20px', fontSize: '13px', fontWeight: 500,
                            cursor: 'pointer', border: '1px solid',
                            borderColor: statusFilter === f.value ? '#3b82f6' : '#e2e8f0',
                            background: statusFilter === f.value ? '#eff6ff' : '#fff',
                            color: statusFilter === f.value ? '#1d4ed8' : '#64748b',
                            transition: 'all 0.15s',
                        }}
                    >
                        {f.label}
                    </button>
                ))}
            </div>

            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
                {isLoading ? (
                    // Scroll horizontal contido também no skeleton, pra não "pular"
                    // de layout assim que os dados reais chegarem.
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                                    {['Nº', 'Título', 'Cliente', 'Técnico', 'Prioridade', 'Status', 'Data'].map((h) => (
                                        <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: '12px', fontWeight: 500, color: '#94a3b8', whiteSpace: 'nowrap' }}>
                                            {h}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {Array.from({ length: 8 }).map((_, i) => (
                                    <tr key={i} style={{ borderTop: i > 0 ? '1px solid #f1f5f9' : 'none' }}>
                                        {Array.from({ length: 7 }).map((_, j) => (
                                            <td key={j} style={{ padding: '12px 16px' }}>
                                                <Skeleton className="h-4 w-full" />
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : orders.length === 0 ? (
                    <div style={{ padding: '60px', textAlign: 'center' }}>
                        <p style={{ fontSize: '15px', fontWeight: 500, color: '#0f172a', margin: '0 0 6px' }}>
                            Nenhuma ordem encontrada
                        </p>
                        <p style={{ fontSize: '13px', color: '#94a3b8', margin: '0 0 16px' }}>
                            {statusFilter ? 'Tente outro filtro de status.' : 'Crie a primeira ordem de serviço.'}
                        </p>
                        {!statusFilter && (
                            <button
                                onClick={() => setShowCreateModal(true)}
                                style={{ fontSize: '13px', color: '#3b82f6', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}
                            >
                                Criar OS →
                            </button>
                        )}
                    </div>
                ) : (
                    <>
                        {/* Scroll horizontal contido — a tabela rola dentro do card,
                            nunca empurra a largura da página inteira. */}
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                                        {['Nº', 'Título', 'Cliente', 'Técnico', 'Prioridade', 'Status', 'Data'].map((h) => (
                                            <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontSize: '12px', fontWeight: 500, color: '#94a3b8', whiteSpace: 'nowrap' }}>
                                                {h}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {orders.map((order: ServiceOrder, i: number) => (
                                        <tr
                                            key={order.id}
                                            onClick={() => navigate(`/orders/${order.id}`)}
                                            style={{ borderTop: i > 0 ? '1px solid #f1f5f9' : 'none', cursor: 'pointer', transition: 'background 0.1s' }}
                                            onMouseEnter={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = '#f8fafc' }}
                                            onMouseLeave={(e) => { (e.currentTarget as HTMLTableRowElement).style.background = 'transparent' }}
                                        >
                                            <td style={{ padding: '12px 16px', fontSize: '13px', color: '#64748b', fontWeight: 500, whiteSpace: 'nowrap' }}>
                                                {formatOrderNumber(order.order_number)}
                                            </td>
                                            <td style={{ padding: '12px 16px', fontSize: '13px', color: '#0f172a', maxWidth: '220px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {order.title}
                                            </td>
                                            <td style={{ padding: '12px 16px', fontSize: '13px', color: '#64748b', maxWidth: '160px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {order.customer_name ?? '—'}
                                            </td>
                                            <td style={{ padding: '12px 16px', fontSize: '13px', color: '#64748b', maxWidth: '140px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {order.technician_name ?? '—'}
                                            </td>
                                            <td style={{ padding: '12px 16px' }}>
                                                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: PRIORITY_COLOR[order.priority] ?? '#64748b', fontWeight: 500, whiteSpace: 'nowrap' }}>
                                                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: PRIORITY_COLOR[order.priority] ?? '#64748b', flexShrink: 0 }} />
                                                    {PRIORITY_LABEL[order.priority] ?? order.priority}
                                                </span>
                                            </td>
                                            <td style={{ padding: '12px 16px' }}>
                                                <span style={{
                                                    display: 'inline-block', padding: '3px 8px', borderRadius: '6px',
                                                    fontSize: '12px', fontWeight: 500, whiteSpace: 'nowrap',
                                                    background: (STATUS_COLOR[order.status] ?? STATUS_COLOR['draft']).bg,
                                                    color: (STATUS_COLOR[order.status] ?? STATUS_COLOR['draft']).text,
                                                }}>
                                                    {STATUS_LABEL[order.status] ?? order.status}
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

                        {totalPages > 1 && (
                            <div style={{ padding: '12px 16px', borderTop: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                                <span style={{ fontSize: '13px', color: '#94a3b8' }}>
                                    Página {page} de {totalPages}
                                </span>
                                <div style={{ display: 'flex', gap: '6px' }}>
                                    <button
                                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                                        disabled={page === 1}
                                        style={{ padding: '5px 12px', borderRadius: '6px', border: '1px solid #e2e8f0', background: '#fff', fontSize: '13px', cursor: page === 1 ? 'not-allowed' : 'pointer', color: page === 1 ? '#cbd5e1' : '#475569' }}
                                    >
                                        ← Anterior
                                    </button>
                                    <button
                                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                                        disabled={page === totalPages}
                                        style={{ padding: '5px 12px', borderRadius: '6px', border: '1px solid #e2e8f0', background: '#fff', fontSize: '13px', cursor: page === totalPages ? 'not-allowed' : 'pointer', color: page === totalPages ? '#cbd5e1' : '#475569' }}
                                    >
                                        Próxima →
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
