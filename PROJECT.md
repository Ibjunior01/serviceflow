# ServiceFlow — Project Continuity Document

## Sessão Atual
**Fase:** 2B — Polimento de UX + Preparação para Deploy
**Status:** Em andamento — validação E2E concluída, skeleton loading pendente

## Progresso das Fases

| Fase | Descrição | Status |
|------|-----------|--------|
| 1A | Estrutura base + Docker + Config | ✅ Concluída |
| 1B | Models SQLAlchemy 2.0 + Alembic | ✅ Concluída |
| 1C | Schemas Pydantic v2 | ✅ Concluída |
| 1D | Auth JWT (login, refresh, dependency) | ✅ Concluída |
| 1E | CRUD Base + Service Layer | ✅ Concluída |
| 1F | Endpoints REST /api/v1 | ✅ Concluída |
| 1G | Testes Automatizados pytest + httpx | ✅ Concluída |
| 2A | Frontend React + Vite + Tailwind — todas as telas | ✅ Concluída |
| 2B | Polimento de UX + Preparação para Deploy | ⏳ Em andamento |

## Decisões de Arquitetura Tomadas
- Async engine (asyncpg) para performance sob carga
- Versionamento de API em /api/v1 desde o início
- Settings via pydantic-settings com validação no boot
- Docker Compose como ambiente padrão (PostgreSQL + FastAPI)
- WSL 2 como engine do Docker no Windows
- UUID v4 como PK em todos os models (gerado pelo Python)
- `lazy="selectin"` em todos os relationships (obrigatório para async)
- `ondelete` explícito em todas as FKs (CASCADE / RESTRICT / SET NULL)
- Totais financeiros calculados no service layer, não no banco
- Alembic rodando fora do Docker (host=localhost no .env local)
- `python -m alembic` como padrão (evita problemas de PATH no Windows)
- `DATABASE_URL` com `postgresql+asyncpg://` para compatibilidade asyncpg
- `email-validator>=2.0.0` adicionado ao requirements.txt
- Schemas em `backend/app/schemas/` com padrão Base/Create/Update/Response por entidade
- `PaginatedResponse[T]` genérico para todas as listagens — exige `total_pages` (usar `ceil`)
- `ServiceOrderSummary` para dashboards
- `ServiceOrderStatusUpdate` em endpoint separado (PATCH /orders/{id}/status)
- `bcrypt==4.0.1` pinado (última versão compatível com passlib)
- Enums com nomes UPPERCASE no Python, valores serializados em lowercase
- `role` mapeado como `String` no banco — passar valor string diretamente (não `.value`)
- Pydantic v2 com `use_enum_values=True` serializa enums para string antes do service layer — nunca chamar `.value` em campos vindos de schemas
- Slug de Company gerado como `slugify(name)-uuid[:8]`
- Auth: `CurrentUser`, `AdminOnly`, `OwnerOnly`, `TechOrAbove` como `Annotated[User, Depends(...)]`
- `require_roles()` retorna `Annotated[User, Depends(_guard)]` — usar como anotação de tipo, nunca dentro de `Depends()`
- Registro cria Company + User(OWNER) + Subscription(TRIALING 14 dias) em transação única
- Refresh token sem blacklist no MVP
- `get_db` é o nome da função de sessão em `app/db/session.py`
- Todos os comandos executados de dentro de `backend/`
- Repository Pattern: `repository` cuida dos queries, `service` cuida da lógica de negócio
- `CRUDBase` genérico com `get`, `get_by`, `list`, `create`, `update`, `delete`, `exists`
- `list()` no CRUDBase retorna `tuple[list[ModelType], int]`
- Repositórios e services instanciados como singletons no módulo
- Exceções de domínio em `app/core/exceptions.py` mapeadas para HTTP no `main.py`
- Máquina de estados da OS em `VALID_TRANSITIONS` no `service_order_service.py`
- Timestamps automáticos: `started_at` (→ IN_PROGRESS), `completed_at` (→ COMPLETED/CANCELLED)
- `get_next_order_number()` usa `MAX(order_number)` por tenant
- `order_number` é `VARCHAR` no banco — migration para `INTEGER` pendente
- Técnico só edita OS atribuída a ele
- OS finalizada (COMPLETED/INVOICED/CANCELLED) não pode ser editada nem deletada
- Apenas DRAFT pode ser excluída
- Apenas OWNER pode alterar roles
- Campos do model `Customer` detalhados (`address_street`, `address_number`, etc.)
- `assigned_to` no schema de OS mapeia para `technician_id` no model
- Testes usam `drop_all/create_all` por teste (sem rollback/truncate — incompatível com asyncpg no Windows)
- `asyncio_default_fixture_loop_scope = function` no pytest.ini (obrigatório para Windows + pytest-asyncio 0.24)
- Login via JSON `{"email": ..., "password": ...}` (não OAuth2 form-data)
- Enums serializados em lowercase pelo Pydantic v2 (`"draft"`, `"admin"`, `"high"`, etc.)
- `service_order_service.list()` monta `PaginatedResponse[ServiceOrderSummary]` manualmente
- Bug corrigido: `companies.py` endpoint usava args posicionais em `company_service.update()`
- Bug corrigido: `user_service.update_role()` chamava `.value` em string já serializada

## Decisões de Frontend (Fase 2A + 2B)
- shadcn/ui com preset `radix-nova` — componentes instalados em `src/components/ui/`
- Atenção: shadcn com `radix-nova` cria pasta física `@` na raiz em vez de usar `src/` — ao adicionar novos componentes, copiar manualmente para `src/components/ui/` ou trocar `"style": "default"` no `components.json`
- `sonner` para notificações toast — importar `toast` de `'sonner'`, usar `toast.success()` / `toast.error()`
- `useToast` do shadcn NÃO existe no projeto — não usar
- `<Toaster richColors position="top-right" />` montado no `main.tsx`
- Axios client em `src/api/client.ts` — importar como `@/api/client` (não `@/lib/api`)
- `useAuthStore` em `src/store/authStore.ts` — expõe `user`, `setUser`, `setTokens`, `logout`
- TanStack Query v5: `isPending` (não `isLoading`) nas mutations
- Hooks de dados em `src/hooks/` — padrão: um arquivo por entidade
- `null` vindo da API não é atribuível a `string | undefined` — converter com `?? undefined` ao passar para forms
- `react-hook-form` + `zod` + `@hookform/resolvers` instalados para validação de formulários
- Enum `priority` no backend usa `normal` (não `medium`) — mapear `normal` → "Média" no frontend
- Campo de nome de usuário na API é `full_name` (não `name`) — AppUser e UserCreate usam `full_name`
- `<select>` nativo no Chrome/Windows ignora `style` em `<option>` — usar componente `CustomSelect` com dropdown feito em JSX para casos onde cor/estilo importa
- `CustomSelect` controlado via `useState` local — não registrar no react-hook-form via `register()`, incluir valor manualmente no payload do `onSubmit`
- Guard de permissão `canCreate`/`canAssign` baseado em `useAuthStore` para esconder ações por role
- Queries com `enabled: canAssign` evitam chamadas 403 desnecessárias para endpoints AdminOnly
- Dropdown do `CustomSelect` abre para cima (`bottom: calc(100% + 4px)`) para evitar corte pelo modal
- Bug corrigido: `assigned_to` não entrava no payload — `CustomSelect` usa `useState`, não RHF
- Bug corrigido: `document: ""` rejeitado pelo validator Pydantic — usar `not v` em vez de `v is None`
- Bug corrigido: query de usuários duplicada no `CreateOrderModal` causava erro de compilação
- Bug corrigido: `toast.error(msg)` explodia quando `detail` era array Pydantic v2 — tratar com `Array.isArray`
- Técnico autônomo deve se cadastrar como `owner` — fluxo natural do registro já garante isso
- `POST /api/v1/orders` permanece `AdminOnly` — técnico autônomo opera como owner

## Stack Técnica
- **Backend:** FastAPI + Python 3.14
- **ORM:** SQLAlchemy 2.0 (DeclarativeBase, Mapped, mapped_column)
- **Banco:** PostgreSQL 16 Alpine via Docker
- **Migrations:** Alembic 1.18.4
- **Validação:** Pydantic v2 + pydantic-settings
- **Auth:** python-jose + passlib + bcrypt==4.0.1
- **Driver async:** asyncpg 0.31.0
- **Testes:** pytest + pytest-asyncio + httpx (AsyncClient)
- **Banco de testes:** PostgreSQL separado via Docker (serviceflow_test)
- **Venv:** .venv em serviceflow/ (raiz do projeto)
- **Frontend:** React 18 + Vite + TypeScript + Tailwind CSS + shadcn/ui
- **Estado global:** Zustand com persist (chave `sf-auth`)
- **Cache/sync:** TanStack Query v5
- **Roteamento:** React Router v6
- **Notificações:** Sonner
- **Formulários:** react-hook-form + zod + @hookform/resolvers

## Planos e Preços
- **Free:** R$ 0/mês
- **Básico:** R$ 67/mês
- **Pro:** R$ 127/mês
- **Empresa:** R$ 247/mês

## Estrutura de Pastas (estado atual)
serviceflow/
├── .venv/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── router.py                          ✅
│   │   │   └── endpoints/
│   │   │       ├── auth.py                        ✅
│   │   │       ├── companies.py                   ✅
│   │   │       ├── users.py                       ✅
│   │   │       ├── customers.py                   ✅
│   │   │       └── service_orders.py              ✅
│   │   ├── core/
│   │   │   ├── config.py                          ✅
│   │   │   ├── security.py                        ✅
│   │   │   ├── dependencies.py                    ✅
│   │   │   └── exceptions.py                      ✅
│   │   ├── db/
│   │   │   ├── session.py                         ✅
│   │   │   └── base.py                            ✅
│   │   ├── models/                                ✅
│   │   ├── repositories/                          ✅
│   │   ├── schemas/                               ✅
│   │   ├── services/                              ✅
│   │   └── main.py                                ✅
│   ├── tests/                                     ✅
│   │   ├── conftest.py                            ✅
│   │   ├── test_auth.py                           ✅
│   │   ├── test_companies.py                      ✅
│   │   ├── test_users.py                          ✅
│   │   ├── test_customers.py                      ✅
│   │   └── test_service_orders.py                 ✅
│   ├── alembic/versions/
│   │   ├── 06d5ab8065eb_initial_schema.py         ✅
│   │   └── xxxx_expand_customer_address_fields.py ✅
│   ├── .env
│   ├── .env.example
│   ├── .env.test                                  ✅
│   ├── pytest.ini                                 ✅
│   ├── alembic.ini
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements.lock
└── frontend/                                      ✅
    ├── src/
    │   ├── api/
    │   │   ├── client.ts                          ✅ (axios + interceptor JWT)
    │   │   ├── auth.ts                            ✅
    │   │   ├── customers.ts                       ✅
    │   │   ├── orders.ts                          ✅ (create, update, delete adicionados)
    │   │   └── users.ts                           ✅
    │   ├── components/
    │   │   ├── layout/
    │   │   │   ├── AppLayout.tsx                  ✅
    │   │   │   ├── Header.tsx                     ✅
    │   │   │   └── Sidebar.tsx                    ✅
    │   │   └── ui/                                ✅ (shadcn/ui components)
    │   ├── hooks/
    │   │   ├── useAuth.ts                         ✅
    │   │   ├── useCompany.ts                      ✅
    │   │   ├── useCustomers.ts                    ✅
    │   │   ├── useOrders.ts                       ✅ (criado do zero nesta sessão)
    │   │   └── useUsers.ts                        ✅ (full_name corrigido)
    │   ├── pages/
    │   │   ├── LoginPage.tsx                      ✅
    │   │   ├── DashboardPage.tsx                  ✅ (priority normal corrigido)
    │   │   ├── OrdersPage.tsx                     ✅ (modal criação + CustomSelect)
    │   │   ├── OrderDetailPage.tsx                ✅
    │   │   ├── CustomersPage.tsx                  ✅
    │   │   ├── UsersPage.tsx                      ✅ (full_name corrigido)
    │   │   └── SettingsPage.tsx                   ✅
    │   ├── router/
    │   │   └── index.tsx                          ✅
    │   ├── store/
    │   │   └── authStore.ts                       ✅
    │   ├── types/
    │   │   └── api.ts                             ✅
    │   └── main.tsx                               ✅ (Toaster montado)
    ├── index.html
    ├── vite.config.ts
    ├── tsconfig.app.json
    ├── tsconfig.json
    ├── components.json
    └── package.json

## Endpoints Implementados (Fase 1F)

### Auth
| Método | Rota | Auth |
|--------|------|------|
| POST | `/api/v1/auth/register` | Público |
| POST | `/api/v1/auth/login` | Público |
| POST | `/api/v1/auth/refresh` | Público |
| GET | `/api/v1/auth/me` | Bearer |

### Companies
| Método | Rota | Auth |
|--------|------|------|
| GET | `/api/v1/companies/me` | CurrentUser |
| PATCH | `/api/v1/companies/me` | OwnerOnly |

### Users
| Método | Rota | Auth |
|--------|------|------|
| GET | `/api/v1/users` | AdminOnly |
| POST | `/api/v1/users` | AdminOnly |
| GET | `/api/v1/users/me` | CurrentUser |
| GET | `/api/v1/users/{id}` | AdminOnly |
| PATCH | `/api/v1/users/{id}` | CurrentUser |
| DELETE | `/api/v1/users/{id}` | OwnerOnly |
| PATCH | `/api/v1/users/{id}/role` | OwnerOnly |

### Customers
| Método | Rota | Auth |
|--------|------|------|
| GET | `/api/v1/customers` | TechOrAbove |
| POST | `/api/v1/customers` | AdminOnly |
| GET | `/api/v1/customers/{id}` | TechOrAbove |
| PATCH | `/api/v1/customers/{id}` | AdminOnly |
| DELETE | `/api/v1/customers/{id}` | AdminOnly |

### Service Orders
| Método | Rota | Auth |
|--------|------|------|
| GET | `/api/v1/orders` | TechOrAbove |
| POST | `/api/v1/orders` | AdminOnly |
| GET | `/api/v1/orders/{id}` | TechOrAbove |
| PATCH | `/api/v1/orders/{id}` | TechOrAbove |
| DELETE | `/api/v1/orders/{id}` | AdminOnly |
| PATCH | `/api/v1/orders/{id}/status` | TechOrAbove |
| GET | `/api/v1/orders/{id}/items` | TechOrAbove |
| POST | `/api/v1/orders/{id}/items` | TechOrAbove |
| DELETE | `/api/v1/orders/{id}/items/{item_id}` | TechOrAbove |

## Fase 2A — Concluída ✅
- Scaffold Vite + React + TypeScript + Tailwind v4 + shadcn/ui
- Zustand auth store com persist no localStorage
- Axios client com interceptor JWT + refresh automático
- React Router v6 com ProtectedRoute
- TanStack Query v5 configurado
- LoginPage — layout split, validação, show/hide senha, erro inline
- AppLayout + Sidebar com NavLink ativo, avatar, logout
- DashboardPage — cards por status, tabela de OS recentes
- OrdersPage — tabela paginada, filtros por status
- OrderDetailPage — dados completos, transição de status, itens com totais
- CustomersPage — listagem paginada, busca, cadastro, edição, exclusão
- UsersPage — listagem, criação, troca de role (OwnerOnly), exclusão
- SettingsPage — dados da empresa, perfil do usuário, assinatura
- Sonner montado no main.tsx (`<Toaster richColors position="top-right" />`)

## Fase 2B — Progresso atual
- [x] Formulário de criação de OS na OrdersPage com modal + react-hook-form + zod
- [x] Validação de formulários com react-hook-form + zod
- [x] Confirmar que todas as telas funcionam com backend rodando (validação E2E completa)
- [x] CustomSelect para contornar limitação do Chrome com `<option>` estilizado
- [x] Guard de permissão por role em botões e campos do formulário
- [x] Correção enum priority: `normal` em vez de `medium`
- [x] Correção campo usuário: `full_name` em vez de `name`
- [x] Correção validator documento cliente: aceitar string vazia como None
- [ ] Verificar se o `authStore` atualiza `user` no store após login (campo `name` no header)
- [ ] Skeleton loading nas tabelas (substituir "Carregando..." por UI real)
- [ ] Empty states com botão de ação direto

## Deploy target
- Frontend: Vercel
- Backend: Hetzner VPS (Fase 3)

## Decisões Pendentes / A Revisar
- [ ] `order_number` como `INTEGER` no banco (atual é VARCHAR)
- [ ] `assigned_to` no schema → renomear para `technician_id` para consistência
- [ ] Avaliar soft delete (`deleted_at`) vs `is_active`
- [ ] Avaliar `RefreshToken` model para blacklist
- [ ] Avaliar `Checklist/ChecklistItem` model (fase 2)
- [ ] Avaliar `computed_field` no config.py para DATABASE_URL automático
- [ ] `components.json` — trocar `"style": "radix-nova"` por `"style": "default"` para evitar bug de instalação de componentes na pasta `@`
- [ ] `tsconfig.app.json` — adicionar `"ignoreDeprecations": "6.0"` para silenciar warning do `baseUrl`
- [ ] Técnico autônomo: documentar no onboarding que deve se cadastrar como owner, sugerindo placeholder "Ex: João Silva Refrigeração" no campo empresa