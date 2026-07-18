import { useState, useEffect } from 'react'
import { Building2, User, CreditCard } from 'lucide-react'
import { useCompany, useUpdateCompany, usePlanUsage, type CompanyUpdate } from '@/hooks/useCompany'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { api } from '@/api/client'
import { toast } from 'sonner'

const PLAN_LABELS: Record<string, string> = {
    free: 'Free',
    basico: 'Básico',
    pro: 'Pro',
    empresa: 'Empresa',
}

const STATUS_META: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' }> = {
    trialing: { label: 'Trial', variant: 'secondary' },
    active: { label: 'Ativo', variant: 'default' },
    past_due: { label: 'Pendente', variant: 'destructive' },
    cancelled: { label: 'Cancelado', variant: 'destructive' },
}

// ── Seção: Dados da Empresa ───────────────────────────────────────────────────
function CompanySection() {
    const { user } = useAuthStore()
    const isOwner = user?.role === 'owner'
    const { data: company, isLoading } = useCompany()
    const updateMutation = useUpdateCompany()

    const [form, setForm] = useState<CompanyUpdate>({})

    useEffect(() => {
        if (company) {
            setForm({
                name: company.name,
                document: company.document ?? '',
                phone: company.phone ?? '',
                email: company.email ?? '',
                address: company.address ?? '',
            })
        }
    }, [company])

    const set = (k: keyof CompanyUpdate) => (e: React.ChangeEvent<HTMLInputElement>) =>
        setForm(f => ({ ...f, [k]: e.target.value }))

    const handleSave = async () => {
        try {
            await updateMutation.mutateAsync(form)
            toast.success('Dados da empresa atualizados.')
        } catch {
            toast.success('Erro ao salvar.')
        }
    }

    if (isLoading) return <p className="text-sm text-muted-foreground">Carregando...</p>

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                    <Label>Nome da Empresa *</Label>
                    <Input value={form.name ?? ''} onChange={set('name')} disabled={!isOwner} />
                </div>
                <div className="space-y-1">
                    <Label>CNPJ / CPF</Label>
                    <Input value={form.document ?? ''} onChange={set('document')} disabled={!isOwner} placeholder="00.000.000/0001-00" />
                </div>
                <div className="space-y-1">
                    <Label>Telefone</Label>
                    <Input value={form.phone ?? ''} onChange={set('phone')} disabled={!isOwner} placeholder="(85) 3333-3333" />
                </div>
                <div className="space-y-1">
                    <Label>E-mail da Empresa</Label>
                    <Input type="email" value={form.email ?? ''} onChange={set('email')} disabled={!isOwner} placeholder="contato@empresa.com" />
                </div>
                <div className="col-span-2 space-y-1">
                    <Label>Endereço</Label>
                    <Input value={form.address ?? ''} onChange={set('address')} disabled={!isOwner} placeholder="Rua, número, bairro, cidade — UF" />
                </div>
            </div>
            {isOwner && (
                <Button onClick={handleSave} disabled={updateMutation.isPending}>
                    {updateMutation.isPending ? 'Salvando...' : 'Salvar Dados da Empresa'}
                </Button>
            )}
        </div>
    )
}

// ── Seção: Meu Perfil ─────────────────────────────────────────────────────────
function ProfileSection() {
    const { user, setUser } = useAuthStore()

    const [form, setForm] = useState({ name: user?.full_name ?? '', email: user?.email ?? '' })
    const [saving, setSaving] = useState(false)

    const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
        setForm(f => ({ ...f, [k]: e.target.value }))

    const handleSave = async () => {
        setSaving(true)
        try {
            const { data } = await api.patch(`/users/${user?.id}`, { name: form.name })
            setUser(data)
            toast.success('Perfil atualizado.')
        } catch {
            toast.success('Erro ao salvar perfil.')
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                    <Label>Nome</Label>
                    <Input value={form.name} onChange={set('name')} />
                </div>
                <div className="space-y-1">
                    <Label>E-mail</Label>
                    <Input value={form.email} disabled className="bg-muted" />
                    <p className="text-xs text-muted-foreground">E-mail não pode ser alterado.</p>
                </div>
            </div>
            <Button onClick={handleSave} disabled={saving}>
                {saving ? 'Salvando...' : 'Salvar Perfil'}
            </Button>
        </div>
    )
}

// ── Seção: Assinatura ─────────────────────────────────────────────────────────
function SubscriptionSection() {
    const { data: company } = useCompany()
    const { data: usage } = usePlanUsage()
    if (!company) return null

    const plan = PLAN_LABELS[company.plan_tier] ?? company.plan_tier
    const statusMeta = company.subscription_status
        ? (STATUS_META[company.subscription_status] ?? { label: company.subscription_status, variant: 'secondary' as const })
        : null

    const daysLeft = company.trial_ends_at
        ? Math.max(0, Math.ceil((new Date(company.trial_ends_at).getTime() - Date.now()) / (1000 * 60 * 60 * 24)))
        : null

    const whatsappMessage = encodeURIComponent(
        `Olá! Tenho interesse em fazer upgrade do plano da minha empresa (${company.name}) no ServiceFlow.`
    )

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-4">
                <div>
                    <p className="text-sm text-muted-foreground">Plano atual</p>
                    <p className="text-lg font-semibold">{plan}</p>
                </div>
                {statusMeta && <Badge variant={statusMeta.variant}>{statusMeta.label}</Badge>}
            </div>

            {company.subscription_status === 'trialing' && daysLeft !== null && (
                <p className="text-sm text-muted-foreground">
                    {daysLeft > 0
                        ? `Seu trial com recursos Pro termina em ${daysLeft} dia${daysLeft === 1 ? '' : 's'}.`
                        : 'Seu trial termina hoje.'}
                </p>
            )}

            {usage && (
                <div className="rounded-lg border p-4 space-y-3">
                    <p className="text-sm font-medium">Uso do plano</p>
                    {[
                        { label: 'Técnicos', used: usage.technicians_used, limit: usage.technicians_limit },
                        { label: 'OS este mês', used: usage.orders_this_month_used, limit: usage.orders_this_month_limit },
                        { label: 'Clientes', used: usage.customers_used, limit: usage.customers_limit },
                    ].map((item) => {
                        const pct = item.limit ? Math.min(100, (item.used / item.limit) * 100) : 0
                        const isNearLimit = item.limit !== null && item.used >= item.limit
                        return (
                            <div key={item.label} className="space-y-1">
                                <div className="flex justify-between text-xs">
                                    <span className="text-muted-foreground">{item.label}</span>
                                    <span className={isNearLimit ? 'text-destructive font-medium' : 'text-muted-foreground'}>
                                        {item.used}{item.limit !== null ? ` / ${item.limit}` : ' (ilimitado)'}
                                    </span>
                                </div>
                                {item.limit !== null && (
                                    <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                                        <div
                                            className={`h-full rounded-full ${isNearLimit ? 'bg-destructive' : 'bg-primary'}`}
                                            style={{ width: `${pct}%` }}
                                        />
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}

            <div className="rounded-lg border p-4 bg-muted/30 space-y-1">
                <p className="text-sm font-medium">Planos disponíveis</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2">
                    {[
                        { key: 'free', label: 'Free', price: 'Grátis' },
                        { key: 'basico', label: 'Básico', price: 'R$ 67/mês' },
                        { key: 'pro', label: 'Pro', price: 'R$ 127/mês' },
                        { key: 'empresa', label: 'Empresa', price: 'R$ 247/mês' },
                    ].map(p => (
                        <div key={p.key}
                            className={`rounded-md border p-3 text-center ${p.key === company.plan_tier ? 'border-primary bg-primary/5' : ''}`}>
                            <p className="text-sm font-medium">{p.label}</p>
                            <p className="text-xs text-muted-foreground">{p.price}</p>
                        </div>
                    ))}
                </div>
            
                <button type="button" onClick={() => window.open(`https://wa.me/5585985649455?text=${whatsappMessage}`, '_blank')} className="inline-block text-xs text-primary underline mt-2">Solicitar upgrade via WhatsApp</button>
        </div>
        </div >
    )
}

// ── Página principal ──────────────────────────────────────────────────────────
export default function SettingsPage() {
    return (
        <div className="p-6 space-y-8 max-w-3xl">
            <div>
                <h1 className="text-2xl font-semibold">Configurações</h1>
                <p className="text-sm text-muted-foreground mt-0.5">Gerencie os dados da empresa e do seu perfil.</p>
            </div>

            <section className="space-y-4">
                <div className="flex items-center gap-2 text-base font-medium">
                    <Building2 className="w-4 h-4" />
                    Dados da Empresa
                </div>
                <Separator />
                <CompanySection />
            </section>

            <section className="space-y-4">
                <div className="flex items-center gap-2 text-base font-medium">
                    <User className="w-4 h-4" />
                    Meu Perfil
                </div>
                <Separator />
                <ProfileSection />
            </section>

            <section className="space-y-4">
                <div className="flex items-center gap-2 text-base font-medium">
                    <CreditCard className="w-4 h-4" />
                    Assinatura
                </div>
                <Separator />
                <SubscriptionSection />
            </section>
        </div>
    )
}