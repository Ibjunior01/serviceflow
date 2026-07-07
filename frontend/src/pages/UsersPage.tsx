import { useState } from 'react'
import { Plus, ShieldCheck, Wrench, Crown, Trash2 } from 'lucide-react'
import {
    useUsers, useCreateUser, useUpdateUserRole, useDeleteUser,
    type AppUser, type UserRole, type UserCreate,
} from '@/hooks/useUsers'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import {
    Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { TableSkeleton } from '@/components/ui/table-skeleton'
import {
    Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog'
import {
    AlertDialog, AlertDialogAction, AlertDialogCancel,
    AlertDialogContent, AlertDialogDescription, AlertDialogFooter,
    AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { toast } from 'sonner'

const ROLE_META: Record<UserRole, { label: string; icon: React.ReactNode; variant: 'default' | 'secondary' | 'outline' }> = {
    owner: { label: 'Proprietário', icon: <Crown className="w-3 h-3" />, variant: 'default' },
    admin: { label: 'Administrador', icon: <ShieldCheck className="w-3 h-3" />, variant: 'secondary' },
    technician: { label: 'Técnico', icon: <Wrench className="w-3 h-3" />, variant: 'outline' },
}

function RoleBadge({ role }: { role: UserRole }) {
    const meta = ROLE_META[role] ?? ROLE_META.technician
    return (
        <Badge variant={meta.variant} className="flex items-center gap-1 w-fit">
            {meta.icon}{meta.label}
        </Badge>
    )
}

function NewUserForm({ onSubmit, loading }: { onSubmit: (v: UserCreate) => void; loading: boolean }) {
    const [form, setForm] = useState<UserCreate>({ full_name: '', email: '', password: '', role: 'technician' })

    const set = (k: keyof UserCreate) => (e: React.ChangeEvent<HTMLInputElement>) =>
        setForm((f: UserCreate) => ({ ...f, [k]: e.target.value }))

    return (
        <form onSubmit={(e) => { e.preventDefault(); onSubmit(form) }} className="space-y-4">
            <div className="space-y-1">
                <Label>Nome *</Label>
                <Input value={form.full_name} onChange={set('full_name')} required placeholder="Nome do usuário" />
            </div>
            <div className="space-y-1">
                <Label>E-mail *</Label>
                <Input type="email" value={form.email} onChange={set('email')} required placeholder="usuario@empresa.com" />
            </div>
            <div className="space-y-1">
                <Label>Senha *</Label>
                <Input type="password" value={form.password} onChange={set('password')} required placeholder="Mínimo 8 caracteres" minLength={8} />
            </div>
            <div className="space-y-1">
                <Label>Perfil</Label>
                <Select value={form.role} onValueChange={(v: string) => setForm((f: UserCreate) => ({ ...f, role: v as UserRole }))}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                        <SelectItem value="technician">Técnico</SelectItem>
                        <SelectItem value="admin">Administrador</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            <DialogFooter>
                <Button type="submit" disabled={loading}>
                    {loading ? 'Criando...' : 'Criar Usuário'}
                </Button>
            </DialogFooter>
        </form>
    )
}

export default function UsersPage() {
    const { user: me } = useAuthStore()
    const isOwner = me?.role === 'owner'
    const isAdmin = me?.role === 'admin' || isOwner

    const [dialogOpen, setDialogOpen] = useState(false)
    const [roleDialogUser, setRoleDialogUser] = useState<AppUser | null>(null)
    const [newRole, setNewRole] = useState<UserRole>('technician')
    const [deletingId, setDeletingId] = useState<string | null>(null)

    const { data, isLoading } = useUsers({ page: 1, page_size: 50 })
    const createMutation = useCreateUser()
    const updateRoleMutation = useUpdateUserRole()
    const deleteMutation = useDeleteUser()

    const users: AppUser[] = data?.items ?? []
    const columnCount = isOwner ? 5 : 4

    const handleCreate = async (payload: UserCreate) => {
        try {
            await createMutation.mutateAsync(payload)
            toast.success('Usuário criado com sucesso.')
            setDialogOpen(false)
        } catch {
            toast.success('Erro ao criar usuário.')
        }
    }

    const handleRoleChange = async () => {
        if (!roleDialogUser) return
        try {
            await updateRoleMutation.mutateAsync({ id: roleDialogUser.id, role: newRole })
            toast.success('Perfil atualizado.')
            setRoleDialogUser(null)
        } catch {
            toast.success('Erro ao alterar perfil.')
        }
    }

    const handleDelete = async () => {
        if (!deletingId) return
        try {
            await deleteMutation.mutateAsync(deletingId)
            toast.success('Usuário removido.')
        } catch {
            toast.success('Erro ao remover usuário.')
        } finally {
            setDeletingId(null)
        }
    }

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-semibold">Usuários</h1>
                    <p className="text-sm text-muted-foreground mt-0.5">
                        {users.length} usuário{users.length !== 1 ? 's' : ''} na equipe
                    </p>
                </div>
                {isAdmin && (
                    <Button onClick={() => setDialogOpen(true)}>
                        <Plus className="w-4 h-4 mr-2" />Novo Usuário
                    </Button>
                )}
            </div>

            <div className="rounded-lg border bg-card">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Nome</TableHead>
                            <TableHead>E-mail</TableHead>
                            <TableHead>Perfil</TableHead>
                            <TableHead>Status</TableHead>
                            {isOwner && <TableHead className="w-[120px]">Ações</TableHead>}
                        </TableRow>
                    </TableHeader>
                    {isLoading ? (
                        <TableSkeleton rows={5} columns={columnCount} />
                    ) : (
                        <TableBody>
                            {users.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={columnCount} className="text-center py-10">
                                        <p className="text-sm font-medium text-foreground mb-1">
                                            Nenhum usuário cadastrado
                                        </p>
                                        <p className="text-sm text-muted-foreground mb-4">
                                            Adicione o primeiro membro da equipe para começar.
                                        </p>
                                        {isAdmin && (
                                            <Button size="sm" onClick={() => setDialogOpen(true)}>
                                                <Plus className="w-4 h-4 mr-2" />
                                                Novo Usuário
                                            </Button>
                                        )}
                                    </TableCell>
                                </TableRow>
                            ) : users.map((u) => (
                                <TableRow key={u.id} className={u.id === me?.id ? 'bg-muted/30' : ''}>
                                    <TableCell className="font-medium">
                                        {u.full_name}
                                        {u.id === me?.id && <span className="ml-2 text-xs text-muted-foreground">(você)</span>}
                                    </TableCell>
                                    <TableCell className="text-muted-foreground">{u.email}</TableCell>
                                    <TableCell><RoleBadge role={u.role} /></TableCell>
                                    <TableCell>
                                        <Badge variant={u.is_active ? 'default' : 'secondary'}>
                                            {u.is_active ? 'Ativo' : 'Inativo'}
                                        </Badge>
                                    </TableCell>
                                    {isOwner && (
                                        <TableCell>
                                            <div className="flex items-center gap-1">
                                                {u.role !== 'owner' && (
                                                    <Button size="sm" variant="outline"
                                                        onClick={() => { setRoleDialogUser(u); setNewRole(u.role) }}>
                                                        Perfil
                                                    </Button>
                                                )}
                                                {u.id !== me?.id && (
                                                    <Button size="icon" variant="ghost"
                                                        className="text-destructive hover:text-destructive"
                                                        onClick={() => setDeletingId(u.id)}>
                                                        <Trash2 className="w-4 h-4" />
                                                    </Button>
                                                )}
                                            </div>
                                        </TableCell>
                                    )}
                                </TableRow>
                            ))}
                        </TableBody>
                    )}
                </Table>
            </div>

            {/* Dialog: novo usuário */}
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                <DialogContent className="max-w-md">
                    <DialogHeader><DialogTitle>Novo Usuário</DialogTitle></DialogHeader>
                    <NewUserForm onSubmit={handleCreate} loading={createMutation.isPending} />
                </DialogContent>
            </Dialog>

            {/* Dialog: alterar role */}
            <Dialog open={!!roleDialogUser} onOpenChange={(open: boolean) => !open && setRoleDialogUser(null)}>
                <DialogContent className="max-w-sm">
                    <DialogHeader>
                        <DialogTitle>Alterar Perfil — {roleDialogUser?.full_name}</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-2">
                        <Select value={newRole} onValueChange={(v: string) => setNewRole(v as UserRole)}>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                                <SelectItem value="technician">Técnico</SelectItem>
                                <SelectItem value="admin">Administrador</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setRoleDialogUser(null)}>Cancelar</Button>
                        <Button onClick={handleRoleChange} disabled={updateRoleMutation.isPending}>
                            {updateRoleMutation.isPending ? 'Salvando...' : 'Confirmar'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* AlertDialog: deletar */}
            <AlertDialog open={!!deletingId} onOpenChange={(open: boolean) => !open && setDeletingId(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>Remover usuário?</AlertDialogTitle>
                        <AlertDialogDescription>
                            O acesso deste usuário ao sistema será revogado permanentemente.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>Cancelar</AlertDialogCancel>
                        <AlertDialogAction onClick={handleDelete}
                            className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                            {deleteMutation.isPending ? 'Removendo...' : 'Remover'}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    )
}