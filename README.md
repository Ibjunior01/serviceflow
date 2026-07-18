# ServiceFlow

> Field Service Management para técnicos de refrigeração e ar-condicionado no Brasil.

**🟢 Em produção:** https://serviceflow-liard.vercel.app

---

## Sumário

- [Sobre o Projeto](#sobre-o-projeto)
- [Stack Técnica](#stack-técnica)
- [Ambientes](#ambientes)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Pré-requisitos](#pré-requisitos)
- [Startup — Passo a Passo (Desenvolvimento Local)](#startup--passo-a-passo-desenvolvimento-local)
- [Comandos Úteis](#comandos-úteis)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Deploy em Produção](#deploy-em-produção)
- [Arquitetura e Decisões Técnicas](#arquitetura-e-decisões-técnicas)
- [Planos e Preços](#planos-e-preços)
- [Progresso das Fases](#progresso-das-fases)
- [Decisões Pendentes](#decisões-pendentes)

---

## Sobre o Projeto

ServiceFlow é um SaaS de gestão de ordens de serviço (OS) voltado para técnicos autônomos e pequenas empresas de refrigeração e ar-condicionado. Permite abertura, agendamento, execução e faturamento de OS, com controle de equipe, itens/peças por ordem e histórico do cliente.

O sistema está **em produção**, publicamente acessível, com backend, frontend e banco de dados reais rodando na nuvem (ver [Deploy em Produção](#deploy-em-produção)).

---

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI + Python 3.14 |
| ORM | SQLAlchemy 2.0 (async) |
| Banco | PostgreSQL 16 (local) / PostgreSQL gerenciado (produção — Render) |
| Migrations | Alembic 1.18.4 |
| Validação | Pydantic v2 + pydantic-settings |
| Auth | python-jose + passlib + bcrypt==4.0.1 |
| Driver async | asyncpg 0.31.0 |
| Ambiente dev | Docker Compose + WSL2 + Windows |
| Testes | pytest + pytest-asyncio + httpx — **68/68 passando** |
| Frontend | React 18 + Vite + TypeScript + Tailwind v4 + shadcn/ui |
| Data fetching | TanStack Query v5 |
| Formulários | React Hook Form + Zod |
| Gráficos | Recharts |
| Deploy backend | Render (Docker, free tier) |
| Deploy frontend | Vercel (free tier) |

---

## Ambientes

| Ambiente | Frontend | Backend | Banco de dados |
|----------|----------|---------|-----------------|
| **Desenvolvimento** (local) | `localhost:5173` (Vite) | `localhost:8000` (Uvicorn) | PostgreSQL via Docker Compose |
| **Produção** | [serviceflow-liard.vercel.app](https://serviceflow-liard.vercel.app) | [serviceflow-backend-5ljk.onrender.com](https://serviceflow-backend-5ljk.onrender.com) | PostgreSQL gerenciado pelo Render |

> ⚠️ **Os bancos de dados de desenvolvimento e produção são completamente independentes.** Dados criados testando localmente não aparecem em produção, e vice-versa. Isso é esperado.

---

## Estrutura de Pastas

```
serviceflow/
├── .venv/                          ← venv na raiz do projeto
├── backend/                        ← ⚠️ comandos de backend rodam daqui
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py             ✅ register, login, refresh, me
│   │   │   ├── companies.py        ✅
│   │   │   ├── customers.py        ✅
│   │   │   ├── orders.py           ✅ CRUD + status (FSM) + items
│   │   │   └── users.py            ✅
│   │   ├── core/
│   │   │   ├── config.py           ✅ pydantic-settings
│   │   │   ├── security.py         ✅ JWT + bcrypt
│   │   │   └── dependencies.py     ✅ get_current_user + RBAC
│   │   ├── db/
│   │   │   ├── session.py          ✅ async session + get_db
│   │   │   └── base.py
│   │   ├── models/                 ✅ completo
│   │   ├── schemas/                ✅ completo
│   │   ├── services/                ✅ completo (auth, customer, order, user, company)
│   │   └── main.py                 ← inclui endpoint /health
│   ├── alembic/versions/           ✅ migrations aplicadas em dev e produção
│   ├── tests/                      ✅ 68 testes
│   ├── .env                        ← desenvolvimento local, não versionar
│   ├── .env.example
│   ├── Dockerfile.prod             ← multi-stage, non-root, usado pelo Render
│   ├── docker-compose.yml          ← desenvolvimento local
│   └── requirements.txt
├── frontend/                       ← ⚠️ comandos de frontend rodam daqui
│   ├── src/
│   │   ├── api/                    ← client.ts (axios + VITE_API_URL), orders.ts, customers.ts, etc.
│   │   ├── components/
│   │   │   ├── layout/             ← AppLayout, Sidebar (drawer mobile)
│   │   │   └── ui/                 ← shadcn/ui
│   │   ├── pages/                  ← Login, Dashboard, Orders, OrderDetail, Customers, Users, Settings
│   │   └── types/api.ts            ← gerado via openapi-typescript
│   ├── .env                        ← desenvolvimento local
│   └── vite.config.ts              ← proxy para backend local em dev
├── docker-compose.prod.yml         ← referência para deploy em VPS (Hetzner) — não usado no Render
├── Caddyfile                       ← referência para deploy em VPS — não usado no Render
└── .env.prod                       ← variáveis de produção locais, não versionado
```

---

## Pré-requisitos

- Python 3.14+
- Node.js 20+ e npm
- Docker Desktop (Windows) + WSL2 habilitado
- Git

---

## Startup — Passo a Passo (Desenvolvimento Local)

> ⚠️ Comandos de backend rodam de dentro de `backend/`; comandos de frontend, de dentro de `frontend/`.

### 1. Abrir o Docker Desktop
Aguarde a baleia ficar verde na barra de tarefas antes de continuar.

### 2. Backend — ativar venv e subir o banco
```powershell
cd C:\Users\<seu-usuario>\Documents\Projetos\serviceflow\backend
..\.venv\Scripts\Activate.ps1
docker compose up -d db
```

### 3. Backend — rodar a API
```powershell
uvicorn app.main:app --reload
```
Acesse o Swagger em `http://localhost:8000/docs`.

### 4. Frontend — rodar o Vite
Em outro terminal:
```powershell
cd C:\Users\<seu-usuario>\Documents\Projetos\serviceflow\frontend
npm run dev
```
Acesse `http://localhost:5173`.

> **Nota:** se o CSS não atualizar após mudanças, verifique se não há um Service Worker fantasma registrado em `localhost:5173` (`DevTools → Application → Service Workers → Unregister` + `Clear site data`). Enquanto não resolvido, valide mudanças de layout em aba anônima.

### Script de startup rápido do backend
Salve como `backend/dev.ps1` e rode com `.\dev.ps1`:
```powershell
docker compose up -d db
Start-Sleep -Seconds 2
uvicorn app.main:app --reload
```

---

## Comandos Úteis

```powershell
# ─── Banco (dev) ─────────────────────────────────────
docker compose up -d db
docker compose exec db psql -U serviceflow -d serviceflow_db -c "\dt"
docker compose exec db psql -U serviceflow -d serviceflow_db -c "SELECT id, full_name, email, role FROM users;"
docker compose exec db psql -U serviceflow -d serviceflow_db -c "SELECT id, name, slug, plan_tier FROM companies;"

# ─── Migrations ──────────────────────────────────────
python -m alembic revision --autogenerate -m "descricao"
python -m alembic upgrade head
python -m alembic downgrade -1

# Rodar migration apontando para o banco de PRODUÇÃO (Render) a partir do local:
# usar a External Database URL, com ?ssl=require obrigatório para asyncpg
$env:DATABASE_URL="postgresql+asyncpg://user:senha@host.oregon-postgres.render.com/db?ssl=require"
alembic upgrade head

# ─── API ─────────────────────────────────────────────
uvicorn app.main:app --reload
docker compose logs -f api

# ─── Testes ──────────────────────────────────────────
cd backend
python -m pytest -v            # todos os testes, verboso
python -m pytest -x -v         # para no primeiro erro
pytest tests/test_auth.py -v   # arquivo específico
pytest tests/ --tb=no -q       # resumo sem traceback

# ─── Frontend ────────────────────────────────────────
cd frontend
npm run dev                    # dev server
npm run build                  # build de produção (roda tsc -b && vite build)
npx tsc --noEmit                # checagem de tipos isolada
```

---

## Variáveis de Ambiente

### Backend — `backend/.env` (desenvolvimento local)

```env
DATABASE_URL=postgresql+asyncpg://serviceflow:senha@localhost:5432/serviceflow_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=serviceflow
POSTGRES_PASSWORD=senha
POSTGRES_DB=serviceflow_db

APP_NAME=ServiceFlow
APP_ENV=development
APP_VERSION=0.1.0

# JWT — gerar com: openssl rand -hex 32 (ou: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=sua_chave_secreta_de_desenvolvimento
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

> ⚠️ Nunca versionar `.env`. Já está no `.gitignore`.

### Backend — Environment Variables no Render (produção)

Configuradas diretamente no painel do Web Service (`serviceflow-backend` → Environment), não em arquivo:

```
APP_NAME=ServiceFlow
APP_ENV=production
APP_VERSION=0.1.0
SECRET_KEY=<chave forte, gerada exclusivamente para produção — nunca reaproveitar a de dev>
POSTGRES_USER=<gerado pelo Render>
POSTGRES_PASSWORD=<gerado pelo Render>
POSTGRES_DB=<gerado pelo Render>
POSTGRES_HOST=<Internal Database URL do Render, sem domínio completo>
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://<user>:<senha>@<host interno>/<db>
CORS_ORIGINS=https://serviceflow-liard.vercel.app
```

### Frontend — `frontend/.env` (desenvolvimento local)

Não é necessário definir `VITE_API_URL` em dev — o `client.ts` cai automaticamente no proxy do Vite (`/api/v1` → `127.0.0.1:8000`, configurado em `vite.config.ts`) quando a variável não existe.

### Frontend — Environment Variable na Vercel (produção)

```
VITE_API_URL=https://serviceflow-backend-5ljk.onrender.com
```

---

## Deploy em Produção

O deploy é feito em duas plataformas gratuitas — **não** no Hetzner originalmente planejado (decisão de custo; ver seção de [Decisões Pendentes](#decisões-pendentes) sobre migração futura).

### Backend + Banco de dados — Render

- **PostgreSQL:** serviço gerenciado do Render, região Oregon.
- **Web Service:** builda a partir de `backend/Dockerfile.prod` (Root Directory: `backend`).
- **Pre-Deploy Command:** `alembic upgrade head` (roda as migrations antes de cada deploy).
- **Health Check Path:** `/health`.
- Deploy automático a cada push na branch `main`.

**Limitações do free tier:**
- O Web Service hiberna após inatividade — a primeira requisição depois de um período ocioso tem latência maior enquanto o container reinicia.
- O PostgreSQL gratuito expira em 90 dias, salvo upgrade — necessário monitorar esse prazo.
- Shell interativo (para comandos manuais) é recurso pago, indisponível no free tier.

### Frontend — Vercel

- Root Directory: `frontend`.
- Framework detectado automaticamente: Vite.
- Deploy automático a cada push na branch `main`.
- Variável `VITE_API_URL` aponta para o backend do Render.

### Rodando uma migration manualmente em produção

Caso o Pre-Deploy Command do Render não rode as migrations corretamente (já ocorreu uma vez no primeiro deploy), é possível rodar manualmente a partir do computador local, usando a **External Database URL** do Render (não a Internal, que só é acessível de dentro da rede do Render):

```powershell
$env:DATABASE_URL="postgresql+asyncpg://usuario:senha@host.oregon-postgres.render.com/db?ssl=require"
alembic upgrade head
```

> ⚠️ `?ssl=require` é obrigatório para o driver `asyncpg` conectar externamente ao Postgres do Render — sem isso, a conexão falha com `InvalidAuthorizationSpecificationError: SSL/TLS required`.

---

## Arquitetura e Decisões Técnicas

| Decisão | Motivo |
|---------|--------|
| Async engine (asyncpg) | Performance sob carga — múltiplos técnicos simultâneos |
| UUID v4 como PK | Gerado pelo Python, sem dependência do banco |
| `lazy="selectin"` em todos os relationships | Obrigatório para SQLAlchemy async |
| `ondelete` explícito em todas as FKs | CASCADE / RESTRICT / SET NULL definidos no model |
| Totais financeiros no service layer | Nunca calculados no banco — facilita auditoria e testes |
| `python -m alembic` | Evita problemas de PATH no Windows |
| Versionamento `/api/v1` desde o início | Backward compatibility futura |
| `bcrypt==4.0.1` pinado | Última versão compatível com passlib |
| Schemas com padrão Base/Create/Update/Response | Separação clara de responsabilidades por camada |
| `PaginatedResponse[T]` genérico | Reutilizável em todas as listagens |
| `ServiceOrderStatusUpdate` em endpoint separado | `PATCH /orders/{id}/status` — status nunca muda junto com outros campos |
| Enums com nomes UPPERCASE, valores lowercase | Padrão Python: `UserRole.OWNER`, valor serializado `"owner"` |
| Slug gerado como `slugify(name)-uuid[:8]` | Unicidade garantida mesmo com nomes iguais |
| `technician_id` (não `assigned_to`) em todas as camadas | Renomeação concluída na Fase 2B; frontend teve resquício do nome antigo como status (`assigned`) corrigido na Fase 3 |
| `order_number` como `INTEGER` puro no banco | Migração de VARCHAR concluída; formatação `OS-0001` é responsabilidade só do frontend |
| `VITE_API_URL` com fallback para proxy do Vite | Permite o mesmo código funcionar em dev (proxy local) e produção (URL real do backend) sem duplicação |

### Tabelas no banco

| Tabela | Model | Descrição |
|--------|-------|-----------|
| companies | Company | Tenant raiz (autônomo ou empresa) |
| users | User | Auth + RBAC |
| customers | Customer | Clientes do tenant |
| service_orders | ServiceOrder | Núcleo do FSM |
| service_items | ServiceItem | Itens/peças por OS |
| subscriptions | Subscription | Controle de plano SaaS |

### Enums

| Enum | Valores |
|------|---------|
| PlanTier | FREE / BASICO / PRO / EMPRESA |
| UserRole | OWNER / ADMIN / TECHNICIAN / VIEWER |
| OrderStatus | DRAFT → SCHEDULED → IN_PROGRESS → COMPLETED → INVOICED / CANCELLED |
| OrderPriority | LOW / NORMAL / HIGH / URGENT |
| ItemType | LABOR / PART / TRAVEL / OTHER |
| SubscriptionStatus | TRIALING / ACTIVE / PAST_DUE / CANCELLED / EXPIRED |

> ⚠️ `OrderStatus` **não possui** (e nunca deve possuir) o valor `assigned` — esse status existiu apenas como resquício em código antigo do frontend e foi removido na Fase 3.

### Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/register` | Cria empresa + owner + subscription trial |
| POST | `/api/v1/auth/login` | Login com e-mail e senha |
| POST | `/api/v1/auth/refresh` | Renova tokens (rotation) |
| GET | `/api/v1/auth/me` | Dados do usuário autenticado |
| GET/POST | `/api/v1/customers` | Listar/criar clientes |
| GET/POST | `/api/v1/orders` | Listar/criar ordens de serviço |
| GET | `/api/v1/orders/{id}` | Detalhe de uma OS |
| PATCH | `/api/v1/orders/{id}/status` | Transição de status (FSM) |
| GET/POST | `/api/v1/orders/{id}/items` | Listar/adicionar itens (peças/serviços) da OS |
| DELETE | `/api/v1/orders/{id}/items/{item_id}` | Remover item da OS |
| GET | `/health` | Health check (usado pelo Render) |

### RBAC — Atalhos de permissão

```python
AdminOnly    # OWNER + ADMIN
OwnerOnly    # OWNER apenas
TechOrAbove  # OWNER + ADMIN + TECHNICIAN
```

---

## Planos e Preços

| Plano | Preço |
|-------|-------|
| Free | R$ 0/mês |
| Básico | R$ 67/mês |
| Pro | R$ 127/mês |
| Empresa | R$ 247/mês |

Novos tenants iniciam com 14 dias de trial no plano Free.




---

## Progresso das Fases

| Fase | Descrição | Status |
|------|-----------|--------|
| 1A–1G | Backend completo (estrutura, models, schemas, auth, CRUD, endpoints, testes) | ✅ Concluída — 68/68 testes |
| 2A | Frontend React + Vite + Tailwind — todas as telas | ✅ Concluída |
| 2B | Polimento de UX + preparação para deploy | ✅ Concluída |
| 3 | Deploy em produção (Render + Vercel) | ✅ **Concluída — sistema em produção e funcional** |

---

## Decisões Pendentes

*(baixa prioridade, pós-deploy)*

- [ ] Avaliar soft delete (`deleted_at`) vs `is_active`
- [ ] Avaliar `RefreshToken` model para blacklist
- [ ] Avaliar `Checklist/ChecklistItem` model (fase futura)
- [ ] Avaliar `computed_field` no `config.py` para `DATABASE_URL` automático
- [ ] Refatorar `OrdersPage.tsx` para usar o componente `<Table>` do shadcn (hoje usa tabela HTML manual com estilo inline)
- [ ] Buscar e remover `console.log` residuais no frontend
- [ ] Testar `UsersPage` logado como técnico (não apenas como owner)
- [ ] Code-splitting por rota no frontend — `npm run build` já emite aviso de chunk >500kB
- [ ] Simplificar fluxo de login eliminando chamada extra a `/auth/me`
- [ ] Refatorar `get_order` manual no backend
- [ ] Exibir `order_number` no header de `OrderDetailPage`
- [ ] Resolver Service Worker fantasma em `localhost:5173` (mascarava testes de CSS)
- [ ] Migrar `LoginPage.tsx`, `Sidebar.tsx`, `AppLayout.tsx` de `style={{}}` inline para Tailwind puro
- [ ] Investigar por que o Pre-Deploy Command (`alembic upgrade head`) não rodou no primeiro deploy do Render
- [ ] Monitorar prazo de 90 dias do PostgreSQL gratuito do Render — decidir upgrade ou migração
- [ ] Avaliar migração para Hetzner (infraestrutura paga, sem cold start/expiração) quando o projeto estiver pronto para clientes pagantes reais
- [ ] Considerar endpoint de agregação dedicado no backend para o gráfico mensal do Dashboard, caso o volume de OS cresça (hoje a agregação é feita client-side sobre até 50 ordens)