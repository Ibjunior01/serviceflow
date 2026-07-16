import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ordersApi } from '@/api/orders'
import type { ServiceOrderDetail } from '@/api/orders'

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
    in_progress: { bg: '#fffbeb', text: '#b45309' },
    completed: { bg: '#f0fdf4', text: '#15803d' },
    invoiced: { bg: '#faf5ff', text: '#7e22ce' },
    cancelled: { bg: '#fef2f2', text: '#dc2626' },
}

const PRIORITY_LABEL: Record<string, string> = {
    low: 'Baixa', medium: 'Média', high: 'Alta', urgent: 'Urgente',
}

const PRIORITY_COLOR: Record<string, string> = {
    low: '#22c55e', medium: '#f59e0b', high: '#ef4444', urgent: '#7c3aed',
}

const VALID_TRANSITIONS: Record<string, ServiceOrderDetail['status'][]> = {
    draft: ['scheduled', 'cancelled'],
    scheduled: ['in_progress', 'cancelled'],
    in_progress: ['completed', 'cancelled'],
    completed: ['invoiced'],
    invoiced: [],
    cancelled: [],
}

const ITEM_TYPE_LABELS: Record<string, string> = {
    labor: 'Mão de obra',
    part: 'Peça',
    travel: 'Deslocamento',
    other: 'Outro',
}

const itemSchema = z.object({
    item_type: z.enum(['labor', 'part', 'travel', 'other']),
    description: z.string().min(1, 'Descrição obrigatória'),
    quantity: z.coerce.number().positive('Quantidade deve ser maior que zero'),
    unit_price: z.coerce.number().nonnegative('Preço não pode ser negativo'),
})

type ItemFormInput = z.input<typeof itemSchema>
type ItemFormData = z.output<typeof itemSchema>

function formatDate(iso?: string) {
    if (!iso) return '—'
    return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

function formatCurrency(value?: number) {
    if (value == null) return '—'
    return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export default function OrderDetailPage() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const [statusMenuOpen, setStatusMenuOpen] = useState(false)
    const [isItemModalOpen, setIsItemModalOpen] = useState(false)

    const { register, handleSubmit, reset, formState: { errors } } = useForm<ItemFormInput, unknown, ItemFormData>({
        resolver: zodResolver(itemSchema),
        defaultValues: { item_type: 'part', description: '', quantity: 1, unit_price: 0 },
    })

    const { data, isLoading, isError } = useQuery({
        queryKey: ['order', id],
        queryFn: () => ordersApi.getById(id!),
        enabled: !!id,
    })

    const { data: itemsData } = useQuery({
        queryKey: ['order-items', id],
        queryFn: () => ordersApi.getItems(id!),
        enabled: !!id,
    })

    const statusMutation = useMutation({
        mutationFn: (status: ServiceOrderDetail['status']) =>
            ordersApi.updateStatus(id!, status),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['order', id] })
            queryClient.invalidateQueries({ queryKey: ['orders'] })
            setStatusMenuOpen(false)
        },
    })

    const addItemMutation = useMutation({
        mutationFn: (data: ItemFormData) => ordersApi.addItem(id!, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['order-items', id] })
            queryClient.invalidateQueries({ queryKey: ['order', id] })
            setIsItemModalOpen(false)
            reset()
        },
    })

    const onSubmitItem = (formData: ItemFormData) => {
        addItemMutation.mutate(formData)
    }

    const order = data?.data
    const items = itemsData?.data ?? []
    const nextStatuses = VALID_TRANSITIONS[order?.status ?? ''] ?? []

    if (isLoading) {
        return (
            <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8', fontSize: '14px' }}>
                Carregando…
            </div>
        )
    }

    if (isError || !order) {
        return (
            <div style={{ padding: '60px', textAlign: 'center' }}>
                <p style={{ fontSize: '15px', color: '#0f172a', fontWeight: 500, marginBottom: '12px' }}>
                    Ordem não encontrada.
                </p>
                <button onClick={() => navigate('/orders')}
                    style={{ fontSize: '13px', color: '#3b82f6', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 500 }}>
                    ← Voltar para ordens
                </button>
            </div>
        )
    }

    const statusColor = STATUS_COLOR[order.status] ?? STATUS_COLOR['draft']

    return (
        <div style={{ maxWidth: '860px' }}>
            {/* Breadcrumb */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '20px', fontSize: '13px', color: '#94a3b8' }}>
                <button onClick={() => navigate('/orders')}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', fontSize: '13px', padding: 0 }}>
                    Ordens de Serviço
                </button>
                <span>/</span>
                <span style={{ color: '#0f172a' }}>#{order.order_number}</span>
            </div>

            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', gap: '16px', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: '200px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px', flexWrap: 'wrap' }}>
                        <h1 style={{ fontSize: '20px', fontWeight: 600, color: '#0f172a', margin: 0, letterSpacing: '-0.02em' }}>
                            {order.title}
                        </h1>
                        <span style={{
                            padding: '3px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 500,
                            background: statusColor.bg, color: statusColor.text,
                        }}>
                            {STATUS_LABEL[order.status] ?? order.status}
                        </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '13px', flexWrap: 'wrap' }}>
                        <span style={{ color: PRIORITY_COLOR[order.priority] ?? '#64748b', fontWeight: 500 }}>
                            ● {PRIORITY_LABEL[order.priority] ?? order.priority}
                        </span>
                        <span style={{ color: '#e2e8f0' }}>·</span>
                        <span style={{ color: '#94a3b8' }}>Criada em {formatDate(order.created_at)}</span>
                    </div>
                </div>

                {nextStatuses.length > 0 && (
                    <div style={{ position: 'relative' }}>
                        <button
                            onClick={() => setStatusMenuOpen((v) => !v)}
                            style={{
                                display: 'flex', alignItems: 'center', gap: '6px',
                                padding: '8px 14px', borderRadius: '8px',
                                background: '#3b82f6', color: '#fff',
                                border: 'none', fontSize: '13px', fontWeight: 500, cursor: 'pointer',
                            }}
                        >
                            Alterar status
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="6 9 12 15 18 9" />
                            </svg>
                        </button>
                        {statusMenuOpen && (
                            <div style={{
                                position: 'absolute', right: 0, top: '42px', zIndex: 10,
                                background: '#fff', border: '1px solid #e2e8f0', borderRadius: '10px',
                                boxShadow: '0 4px 16px rgba(0,0,0,0.08)', minWidth: '180px', maxWidth: 'min(180px, calc(100vw - 32px))', overflow: 'hidden',
                            }}>
                                {nextStatuses.map((s) => (
                                    <button
                                        key={s}
                                        onClick={() => statusMutation.mutate(s)}
                                        disabled={statusMutation.isPending}
                                        style={{
                                            display: 'block', width: '100%', textAlign: 'left',
                                            padding: '10px 14px', border: 'none', background: 'none',
                                            fontSize: '13px', cursor: 'pointer', color: '#0f172a',
                                        }}
                                        onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = '#f8fafc' }}
                                        onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = 'none' }}
                                    >
                                        → {STATUS_LABEL[s]}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Cards de info */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
                <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px 20px' }}>
                    <p style={{ fontSize: '11px', fontWeight: 500, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 10px' }}>
                        Cliente
                    </p>
                    <p style={{ fontSize: '15px', fontWeight: 500, color: '#0f172a', margin: '0 0 2px' }}>
                        {order.customer_name ?? '—'}
                    </p>
                </div>

                <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px 20px' }}>
                    <p style={{ fontSize: '11px', fontWeight: 500, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 10px' }}>
                        Técnico responsável
                    </p>
                    <p style={{ fontSize: '15px', fontWeight: 500, color: '#0f172a', margin: '0 0 2px' }}>
                        {order.technician_name ?? '—'}
                    </p>
                </div>

                <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px 20px' }}>
                    <p style={{ fontSize: '11px', fontWeight: 500, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 10px' }}>
                        Datas
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {[
                            { label: 'Agendada', value: formatDate(order.scheduled_at) },
                            { label: 'Iniciada', value: formatDate(order.started_at) },
                            { label: 'Concluída', value: formatDate(order.completed_at) },
                        ].map((d) => (
                            <div key={d.label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                                <span style={{ color: '#94a3b8' }}>{d.label}</span>
                                <span style={{ color: '#0f172a', fontWeight: d.value !== '—' ? 500 : 400 }}>{d.value}</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px 20px' }}>
                    <p style={{ fontSize: '11px', fontWeight: 500, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 10px' }}>
                        Valor total
                    </p>
                    <p style={{ fontSize: '24px', fontWeight: 600, color: '#0f172a', margin: 0, letterSpacing: '-0.025em' }}>
                        {formatCurrency(order.total_amount)}
                    </p>
                </div>
            </div>

            {/* Descrição */}
            {order.description && (
                <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px 20px', marginBottom: '20px' }}>
                    <p style={{ fontSize: '11px', fontWeight: 500, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.07em', margin: '0 0 10px' }}>
                        Descrição
                    </p>
                    <p style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap' }}>
                        {order.description}
                    </p>
                </div>
            )}

            {/* Itens */}
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
                <div style={{ padding: '14px 20px', borderBottom: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 style={{ fontSize: '14px', fontWeight: 600, color: '#0f172a', margin: 0 }}>
                        Itens da ordem
                    </h2>
                    <button
                        onClick={() => setIsItemModalOpen(true)}
                        style={{ fontSize: '13px', fontWeight: 500, color: '#3b82f6', background: 'none', border: 'none', cursor: 'pointer', padding: '4px 8px' }}
                    >
                        + Adicionar item
                    </button>
                </div>
                {items.length === 0 ? (
                    <div style={{ padding: '32px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
                        Nenhum item adicionado.
                    </div>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ background: '#f8fafc' }}>
                                    {['Descrição', 'Qtd', 'Preço unit.', 'Total'].map((h) => (
                                        <th key={h} style={{ padding: '10px 16px', textAlign: h === 'Descrição' ? 'left' : 'right', fontSize: '12px', fontWeight: 500, color: '#94a3b8', whiteSpace: 'nowrap' }}>
                                            {h}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item, i) => (
                                    <tr key={item.id} style={{ borderTop: i > 0 ? '1px solid #f1f5f9' : 'none' }}>
                                        <td style={{ padding: '12px 16px', fontSize: '13px', color: '#0f172a', whiteSpace: 'nowrap' }}>{item.description}</td>
                                        <td style={{ padding: '12px 16px', fontSize: '13px', color: '#64748b', textAlign: 'right', whiteSpace: 'nowrap' }}>{item.quantity}</td>
                                        <td style={{ padding: '12px 16px', fontSize: '13px', color: '#64748b', textAlign: 'right', whiteSpace: 'nowrap' }}>{formatCurrency(item.unit_price)}</td>
                                        <td style={{ padding: '12px 16px', fontSize: '13px', color: '#0f172a', fontWeight: 500, textAlign: 'right', whiteSpace: 'nowrap' }}>{formatCurrency(item.total_price)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Modal — Adicionar item */}
            {isItemModalOpen && (
                <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '16px' }}>
                    <div style={{ background: '#fff', borderRadius: '12px', width: '100%', maxWidth: '420px', maxHeight: 'calc(100vh - 32px)', overflowY: 'auto', padding: '24px' }}>
                        <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '16px' }}>Adicionar item</h3>
                        <form onSubmit={handleSubmit(onSubmitItem)}>
                            <div style={{ marginBottom: '12px' }}>
                                <label style={{ fontSize: '13px', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Tipo</label>
                                <select {...register('item_type')} style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                                    {Object.entries(ITEM_TYPE_LABELS).map(([value, label]) => (
                                        <option key={value} value={value}>{label}</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ marginBottom: '12px' }}>
                                <label style={{ fontSize: '13px', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Descrição</label>
                                <input {...register('description')} style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #e2e8f0' }} />
                                {errors.description && <span style={{ color: '#ef4444', fontSize: '12px' }}>{errors.description.message}</span>}
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                                <div>
                                    <label style={{ fontSize: '13px', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Quantidade</label>
                                    <input type="number" step="0.01" {...register('quantity')} style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #e2e8f0' }} />
                                    {errors.quantity && <span style={{ color: '#ef4444', fontSize: '12px' }}>{errors.quantity.message}</span>}
                                </div>
                                <div>
                                    <label style={{ fontSize: '13px', fontWeight: 500, display: 'block', marginBottom: '4px' }}>Preço unit.</label>
                                    <input type="number" step="0.01" {...register('unit_price')} style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid #e2e8f0' }} />
                                    {errors.unit_price && <span style={{ color: '#ef4444', fontSize: '12px' }}>{errors.unit_price.message}</span>}
                                </div>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                                <button type="button" onClick={() => setIsItemModalOpen(false)} style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#fff', cursor: 'pointer' }}>
                                    Cancelar
                                </button>
                                <button type="submit" disabled={addItemMutation.isPending} style={{ padding: '8px 16px', borderRadius: '8px', border: 'none', background: '#3b82f6', color: '#fff', cursor: 'pointer' }}>
                                    {addItemMutation.isPending ? 'Salvando...' : 'Adicionar'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}