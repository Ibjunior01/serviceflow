import { useState } from 'react'
import { Plus, Search, Pencil, Trash2, Phone, Mail, MapPin } from 'lucide-react'
import {
    useCustomers, useCreateCustomer, useUpdateCustomer, useDeleteCustomer,
    type Customer, type CustomerCreate,
} from '@/hooks/useCustomers'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
    Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog'
import {
    AlertDialog, AlertDialogAction, AlertDialogCancel,
    AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
    AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Label } from '@/components/ui/label'
import { toast } from 'sonner'
import { useAuthStore } from '@/store/authStore'
import { TableSkeleton } from '@/components/ui/table-skeleton'


function CustomerForm({
    initial,
    onSubmit,
    loading,
}: {
    initial?: Partial<CustomerCreate>
    onSubmit: (v: CustomerCreate) => void
    loading: boolean
}) {
    const [form, setForm] = useState<CustomerCreate>({
        name: initial?.name ?? '',
        email: initial?.email ?? '',
        phone: initial?.phone ?? '',
        document: initial?.document ?? '',
        address_street: initial?.address_street ?? '',
        address_number: initial?.address_number ?? '',
        address_complement: initial?.address_complement ?? '',
        address_neighborhood: initial?.address_neighborhood ?? '',
        address_city: initial?.address_city ?? '',
        address_state: initial?.address_state ?? '',
        address_zip: initial?.address_zip ?? '',
    })

    const set = (k: keyof CustomerCreate) => (e: React.ChangeEvent<HTMLInputElement>) =>
        setForm((f) => ({ ...f, [k]: e.target.value }))

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault()
        onSubmit(form)
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2 space-y-1">
                    <Label>Nome *</Label>
                    <Input value={form.name} onChange={set('name')} required placeholder="Nome completo ou razão social" />
                </div>
                <div className="space-y-1">
                    <Label>E-mail</Label>
                    <Input type="email" value={form.email} onChange={set('email')} placeholder="cliente@email.com" />
                </div>
                <div className="space-y-1">
                    <Label>Telefone</Label>
                    <Input value={form.phone} onChange={set('phone')} placeholder="(85) 99999-9999" />
                </div>
                <div className="col-span-2 space-y-1">
                    <Label>CPF / CNPJ</Label>
                    <Input value={form.document} onChange={set('document')} placeholder="000.000.000-00" />
                </div>
            </div>
            <div className="border-t pt-3">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-3">Endereço</p>
                <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-2 space-y-1">
                        <Label>Rua</Label>
                        <Input value={form.address_street} onChange={set('address_street')} placeholder="Rua das Flores" />
                    </div>
                    <div className="space-y-1">
                        <Label>Número</Label>
                        <Input value={form.address_number} onChange={set('address_number')} placeholder="123" />
                    </div>
                    <div className="space-y-1">
                        <Label>Complemento</Label>
                        <Input value={form.address_complement} onChange={set('address_complement')} placeholder="Apto 4" />
                    </div>
                    <div className="space-y-1">
                        <Label>Bairro</Label>
                        <Input value={form.address_neighborhood} onChange={set('address_neighborhood')} placeholder="Centro" />
                    </div>
                    <div className="space-y-1">
                        <Label>CEP</Label>
                        <Input value={form.address_zip} onChange={set('address_zip')} placeholder="60000-000" />
                    </div>
                    <div className="space-y-1">
                        <Label>Cidade</Label>
                        <Input value={form.address_city} onChange={set('address_city')} placeholder="Fortaleza" />
                    </div>
                    <div className="space-y-1">
                        <Label>Estado</Label>
                        <Input value={form.address_state} onChange={set('address_state')} placeholder="CE" maxLength={2} />
                    </div>
                </div>
            </div>
            <DialogFooter>
                <Button type="submit" disabled={loading}>
                    {loading ? 'Salvando...' : 'Salvar'}
                </Button>
            </DialogFooter>
        </form>
    )
}

export default function CustomersPage() {
    const { user } = useAuthStore()
    const isAdmin = user?.role === 'admin' || user?.role === 'owner'

    const [search, setSearch] = useState('')
    const [page, setPage] = useState(1)
    const [dialogOpen, setDialogOpen] = useState(false)
    const [editing, setEditing] = useState<Customer | null>(null)
    const [deletingId, setDeletingId] = useState<string | null>(null)

    const { data, isLoading } = useCustomers({ page, page_size: 15, search: search || undefined })
    const createMutation = useCreateCustomer()
    const updateMutation = useUpdateCustomer()
    const deleteMutation = useDeleteCustomer()


    const openCreate = () => { setEditing(null); setDialogOpen(true) }
    const openEdit = (c: Customer) => { setEditing(c); setDialogOpen(true) }

    const handleSubmit = async (payload: CustomerCreate) => {
        try {
            if (editing) {
                await updateMutation.mutateAsync({ id: editing.id, payload })
                toast.success('Cliente atualizado com sucesso.')
            } else {
                await createMutation.mutateAsync(payload)
                toast.success('Cliente cadastrado com sucesso.')
            }
            setDialogOpen(false)
        } catch {
            toast.error('Erro ao salvar cliente.')
        }
    }

    const handleDelete = async () => {
        if (!deletingId) return
        try {
            await deleteMutation.mutateAsync(deletingId)
            toast.success('Cliente removido.')
        } catch {
            toast.error('Erro ao remover cliente.')
        } finally {
            setDeletingId(null)
        }
    }

    // null → undefined para compatibilidade com CustomerCreate
    const editingAsInitial = editing ? {
        name: editing.name,
        email: editing.email ?? undefined,
        phone: editing.phone ?? undefined,
        document: editing.document ?? undefined,
        address_street: editing.address_street ?? undefined,
        address_number: editing.address_number ?? undefined,
        address_complement: editing.address_complement ?? undefined,
        address_neighborhood: editing.address_neighborhood ?? undefined,
        address_city: editing.address_city ?? undefined,
        address_state: editing.address_state ?? undefined,
        address_zip: editing.address_zip ?? undefined,
    } : undefined

    const customers: Customer[] = data?.items ?? []
    const totalPages: number = data?.total_pages ?? 1

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-semibold">Clientes</h1>
                    <p className="text-sm text-muted-foreground mt-0.5">{data?.total ?? 0} clientes cadastrados</p>
                </div>
                {isAdmin && (
                    <Button onClick={openCreate}>
                        <Plus className="w-4 h-4 mr-2" />
                        Novo Cliente
                    </Button>
                )}
            </div>

            <div className="relative max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                    className="pl-9"
                    placeholder="Buscar por nome ou e-mail..."
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(1) }}
                />
            </div>

            <div className="rounded-lg border bg-card">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Nome</TableHead>
                            <TableHead>Contato</TableHead>
                            <TableHead>Localização</TableHead>
                            <TableHead>Documento</TableHead>
                            {isAdmin && <TableHead className="w-[100px]">Ações</TableHead>}
                        </TableRow>
                    </TableHeader>
                    {isLoading ? (
                        <TableSkeleton rows={6} columns={isAdmin ? 5 : 4} />
                    ) : (
                        <TableBody>
                            {customers.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={isAdmin ? 5 : 4} className="text-center py-10">
                                        <p className="text-sm font-medium text-foreground mb-1">
                                            {search ? 'Nenhum cliente encontrado' : 'Nenhum cliente cadastrado'}
                                        </p>
                                        <p className="text-sm text-muted-foreground mb-4">
                                            {search ? 'Tente outro termo de busca.' : 'Cadastre o primeiro cliente para começar.'}
                                        </p>
                                        {!search && isAdmin && (
                                            <Button size="sm" onClick={openCreate}>
                                                <Plus className="w-4 h-4 mr-2" />
                                                Novo Cliente
                                            </Button>
                                        )}
                                    </TableCell>
                                </TableRow>
                            ) : customers.map((c) => (
                                <TableRow key={c.id}>
                                    <TableCell className="font-medium">{c.name}</TableCell>
                                    <TableCell>
                                        <div className="flex flex-col gap-0.5 text-sm text-muted-foreground">
                                            {c.email && <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{c.email}</span>}
                                            {c.phone && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{c.phone}</span>}
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        {(c.address_city || c.address_state) ? (
                                            <span className="flex items-center gap-1 text-sm text-muted-foreground">
                                                <MapPin className="w-3 h-3" />
                                                {[c.address_city, c.address_state].filter(Boolean).join(' — ')}
                                            </span>
                                        ) : <span className="text-muted-foreground text-sm">—</span>}
                                    </TableCell>
                                    <TableCell>
                                        {c.document
                                            ? <Badge variant="outline">{c.document}</Badge>
                                            : <span className="text-muted-foreground text-sm">—</span>}
                                    </TableCell>
                                    {isAdmin && (
                                        <TableCell>
                                            <div className="flex items-center gap-1">
                                                <Button size="icon" variant="ghost" onClick={() => openEdit(c)}>
                                                    <Pencil className="w-4 h-4" />
                                                </Button>
                                                <Button size="icon" variant="ghost"
                                                    className="text-destructive hover:text-destructive"
                                                    onClick={() => setDeletingId(c.id)}>
                                                    <Trash2 className="w-4 h-4" />
                                                </Button>
                                            </div>
                                        </TableCell>
                                    )}
                                </TableRow>
                            ))}
                        </TableBody>
                    )}
                </Table>
            </div>

            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2">
                    <Button variant="outline" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
                        Anterior
                    </Button>
                    <span className="text-sm text-muted-foreground">Página {page} de {totalPages}</span>
                    <Button variant="outline" size="sm" disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>
                        Próxima
                    </Button>
                </div>
            )}

            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle>{editing ? 'Editar Cliente' : 'Novo Cliente'}</DialogTitle>
                    </DialogHeader>
                    <CustomerForm
                        initial={editingAsInitial}
                        onSubmit={handleSubmit}
                        loading={createMutation.isPending || updateMutation.isPending}
                    />
                </DialogContent>
            </Dialog>

            <AlertDialog open={!!deletingId} onOpenChange={(open: boolean) => !open && setDeletingId(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Remover cliente?</AlertDialogTitle>
                        <AlertDialogDescription>
                            Esta ação não pode ser desfeita. O cliente será permanentemente removido.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancelar</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDelete}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                            {deleteMutation.isPending ? 'Removendo...' : 'Remover'}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    )
}