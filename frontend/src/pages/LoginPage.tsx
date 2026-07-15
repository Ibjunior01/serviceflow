import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/api/auth'

export default function LoginPage() {
    const navigate = useNavigate()
    const { setTokens, setUser } = useAuthStore()

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [showPassword, setShowPassword] = useState(false)

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            const { data: auth } = await authApi.login({ email, password })
            setTokens(auth.access_token, auth.refresh_token)
            const { data: me } = await authApi.me()
            setUser(me)
            navigate('/')
        } catch (err: unknown) {
            const axiosErr = err as { response?: { status?: number } }
            if (axiosErr?.response?.status === 401) {
                setError('E-mail ou senha incorretos.')
            } else {
                setError('Não foi possível conectar ao servidor. Tente novamente.')
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{ minHeight: '100vh', display: 'flex', backgroundColor: '#f8fafc' }}>
            {/* Painel esquerdo — escondido em mobile (abaixo de 768px), visível a partir de md */}
            <div
                className="hidden md:flex md:flex-none md:w-[420px] flex-col justify-between p-12"
                style={{ background: '#0f172a' }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                            <path d="M3 9L7 13L15 5" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>
                    <span style={{ color: '#f8fafc', fontWeight: 600, fontSize: '16px' }}>ServiceFlow</span>
                </div>

                <div>
                    <p style={{ color: '#64748b', fontSize: '11px', fontWeight: 500, letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '20px' }}>
                        Campo de serviço
                    </p>
                    <h1 style={{ color: '#f8fafc', fontSize: '32px', fontWeight: 600, lineHeight: 1.25, letterSpacing: '-0.03em', marginBottom: '20px' }}>
                        Gestão de ordens<br />para equipes técnicas.
                    </h1>
                    <p style={{ color: '#94a3b8', fontSize: '15px', lineHeight: 1.6, maxWidth: '300px' }}>
                        Controle OS, técnicos e clientes num só lugar — do atendimento ao faturamento.
                    </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    {[
                        { value: 'Multi-empresa', label: 'Isolamento total de dados' },
                        { value: 'Tempo real', label: 'Status das OS atualizado' },
                        { value: 'RBAC', label: 'Controle de acesso por perfil' },
                        { value: 'API REST', label: 'Integrável com outros sistemas' },
                    ].map((s) => (
                        <div key={s.label} style={{ background: 'rgba(255,255,255,0.04)', border: '0.5px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '14px 16px' }}>
                            <p style={{ color: '#f8fafc', fontSize: '13px', fontWeight: 600, margin: '0 0 3px' }}>{s.value}</p>
                            <p style={{ color: '#64748b', fontSize: '12px', margin: 0, lineHeight: 1.4 }}>{s.label}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Painel direito — padding reduzido em mobile via className, mantém 48px em desktop */}
            <div
                className="px-4 py-8 md:px-12 md:py-12"
                style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
                <div style={{ width: '100%', maxWidth: '380px' }}>
                    <h2 style={{ color: '#0f172a', fontSize: '22px', fontWeight: 600, letterSpacing: '-0.025em', margin: '0 0 6px' }}>
                        Entrar na conta
                    </h2>
                    <p style={{ color: '#64748b', fontSize: '14px', margin: '0 0 32px' }}>
                        Use suas credenciais de acesso para continuar.
                    </p>

                    <form onSubmit={handleSubmit} noValidate>
                        <div style={{ marginBottom: '16px' }}>
                            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#0f172a', marginBottom: '6px' }}>
                                E-mail
                            </label>
                            <input
                                type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                                placeholder="nome@empresa.com" required autoComplete="email"
                                style={{ width: '100%', height: '40px', padding: '0 12px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#fff', color: '#0f172a', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }}
                                onFocus={(e) => { e.target.style.borderColor = '#3b82f6' }}
                                onBlur={(e) => { e.target.style.borderColor = '#e2e8f0' }}
                            />
                        </div>

                        <div style={{ marginBottom: '24px' }}>
                            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: '#0f172a', marginBottom: '6px' }}>
                                Senha
                            </label>
                            <div style={{ position: 'relative' }}>
                                <input
                                    type={showPassword ? 'text' : 'password'} value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••" required autoComplete="current-password"
                                    style={{ width: '100%', height: '40px', padding: '0 40px 0 12px', borderRadius: '8px', border: '1px solid #e2e8f0', background: '#fff', color: '#0f172a', fontSize: '14px', outline: 'none', boxSizing: 'border-box' }}
                                    onFocus={(e) => { e.target.style.borderColor = '#3b82f6' }}
                                    onBlur={(e) => { e.target.style.borderColor = '#e2e8f0' }}
                                />
                                <button type="button" onClick={() => setShowPassword(!showPassword)}
                                    style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', padding: '4px', display: 'flex', alignItems: 'center' }}
                                    aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}>
                                    {showPassword ? (
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                                            <line x1="1" y1="1" x2="23" y2="23" />
                                        </svg>
                                    ) : (
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                            <circle cx="12" cy="12" r="3" />
                                        </svg>
                                    )}
                                </button>
                            </div>
                        </div>

                        {error && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 12px', borderRadius: '8px', background: '#fef2f2', border: '1px solid #fecaca', marginBottom: '16px' }}>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                                    <circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" />
                                </svg>
                                <span style={{ fontSize: '13px', color: '#dc2626' }}>{error}</span>
                            </div>
                        )}

                        <button type="submit" disabled={loading || !email || !password}
                            style={{ width: '100%', height: '40px', borderRadius: '8px', background: loading || !email || !password ? '#e2e8f0' : '#3b82f6', color: loading || !email || !password ? '#94a3b8' : '#fff', border: 'none', fontSize: '14px', fontWeight: 500, cursor: loading || !email || !password ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                            {loading ? 'Entrando…' : 'Entrar'}
                        </button>
                    </form>

                    <p style={{ marginTop: '32px', fontSize: '12px', color: '#94a3b8', textAlign: 'center' }}>
                        ServiceFlow © {new Date().getFullYear()} — Gestão de campo para refrigeração e ar-condicionado
                    </p>
                </div>
            </div>
        </div>
    )
}
