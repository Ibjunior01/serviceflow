import { useState, useEffect } from 'react'
import { Building2, User, CreditCard } from 'lucide-react'
import { useCompany, useUpdateCompany, type CompanyUpdate } from '@/hooks/useCompany'
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
    basic: 'Básico',
    pro: 'Pro',
    enterprise: 'Empresa',
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
           toast.success('Dados da empresa atualizados.' )
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
    
    const [form, setForm] = useState({ name: user?.name ?? '', email: user?.email ?? '' })
    const [saving, setSaving] = useState(false)

    const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
        setForm(f => ({ ...f, [k]: e.target.value }))

    const handleSave = async () => {
        setSaving(true)
        try {
            const { data } = await api.patch(`/users/${user?.id}`, { name: form.name })
            setUser(data) // atualiza store
           toast.success('Perfil atualizado.' )
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
    if (!company) return null

    const plan = PLAN_LABELS[company.subscription_plan] ?? company.subscription_plan
    const statusMeta = STATUS_META[company.subscription_status] ?? { label: company.subscription_status, variant: 'secondary' as const }

    return (
        <div className="space-y-4">
            <div className="flex items-center gap-4">
                <div>
                    <p className="text-sm text-muted-foreground">Plano atual</p>
                    <p className="text-lg font-semibold">{plan}</p>
                </div>
                <Badge variant={statusMeta.variant}>{statusMeta.label}</Badge>
            </div>

            {company.trial_ends_at && company.subscription_status === 'trialing' && (
                <p className="text-sm text-muted-foreground">
                    Trial expira em: {new Date(company.trial_ends_at).toLocaleDateString('pt-BR')}
                </p>
            )}

            <div className="rounded-lg border p-4 bg-muted/30 space-y-1">
                <p className="text-sm font-medium">Planos disponíveis</p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2">
                    {[
                        { key: 'free', label: 'Free', price: 'Grátis' },
                        { key: 'basic', label: 'Básico', price: 'R$ 67/mês' },
                        { key: 'pro', label: 'Pro', price: 'R$ 127/mês' },
                        { key: 'enterprise', label: 'Empresa', price: 'R$ 247/mês' },
                    ].map(p => (
                        <div key={p.key}
                            className={`rounded-md border p-3 text-center ${p.key === company.subscription_plan ? 'border-primary bg-primary/5' : ''}`}>
                            <p className="text-sm font-medium">{p.label}</p>
                            <p className="text-xs text-muted-foreground">{p.price}</p>
                        </div>
                    ))}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                    Para fazer upgrade, entre em contato com o suporte.
                </p>
            </div>
        </div>
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

            {/* Empresa */}
            <section className="space-y-4">
                <div className="flex items-center gap-2 text-base font-medium">
                    <Building2 className="w-4 h-4" />
                    Dados da Empresa
                </div>
                <Separator />
                <CompanySection />
            </section>

            {/* Perfil */}
            <section className="space-y-4">
                <div className="flex items-center gap-2 text-base font-medium">
                    <User className="w-4 h-4" />
                    Meu Perfil
                </div>
                <Separator />
                <ProfileSection />
            </section>

            {/* Assinatura */}
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