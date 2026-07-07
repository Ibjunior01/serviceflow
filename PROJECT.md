# ServiceFlow — Project Continuity Document

## Sessão Atual
**Fase:** 3 — Preparação para Deploy (Backend + Frontend)
**Status:** Fase 2B concluída integralmente (skeleton loading, empty states, limpeza de debug). Início da Fase 3: preparar backend e frontend para produção (Hetzner VPS + Vercel).

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
| 2B | Polimento de UX + Preparação para Deploy | ✅ Concluída |
| 3  | Deploy — Backend (Hetzner) + Frontend (Vercel) | ⏳ Em andamento |

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
- Confirmado: a pasta real do projeto é `src/components/` (inglês), não `src/componentes/` — o alias `@` no import (`@/components/ui/...`) é resolvido via `vite.config.ts`/`tsconfig.json`, não corresponde a uma pasta física chamada `@`
- `sonner` para notificações toast — importar `toast` de `'sonner'`, usar `toast.success()` / `toast.error()`
- `useToast` do shadcn NÃO existe no projeto — não usar
- `<Toaster richColors position="top-right" />` montado no `main.tsx`
- Axios client em `src/api/client.ts` — importar como `@/api/client` (não `@/lib/api`)
- `useAuthStore` em `src/store/authStore.ts` — expõe `user`, `setUser`, `setTokens`, `logout`
- TanStack Query v5: `isPending` (não `isLoading`) nas mutations; `isLoading` continua correto para queries
- Hooks de dados em `src/hooks/` — padrão: um arquivo por entidade
- `null` vindo da API não é atribuível a `string | undefined` — converter com `?? undefined` ao passar para forms
- `react-hook-form` + `zod` + `@hookform/resolvers` instalados para validação de formulários
- Enum `priority` no backend usa `normal` (não `medium`) — mapear `normal` → "Média" no frontend
- Campo de nome de usuário na API é `full_name` (não `name`) — ver seção de bugs abaixo, esse padrão se repetiu em 4 arquivos diferentes
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
- `Header.tsx` não existe fisicamente — o header/perfil de usuário é renderizado dentro de `Sidebar.tsx` (rodapé "User footer")
- `src/types/api.ts` está vazio — cada arquivo (`authStore.ts`, `api/auth.ts`, hooks) define seus próprios tipos de forma independente, causa raiz da cadeia de bugs `name`/`full_name`. **Pendente antes do deploy** (ver Decisões Pendentes da Fase 3).
- `hooks/useAuth.ts` está vazio e não é importado em lugar nenhum — código morto do scaffold da Fase 2A, nunca implementado
- **`OrdersPage.tsx` é estruturalmente diferente das outras páginas**: usa `<table>` HTML pura com estilos inline (`style={{...}}`), não os componentes shadcn `<Table>/<TableBody>/<TableRow>` usados em `UsersPage.tsx` e `CustomersPage.tsx` — dívida técnica documentada, não urgente

## Bugs corrigidos na sessão de 2B.2 (cadeia name vs full_name)
Causa raiz: `src/types/api.ts` vazio, então tipos de usuário duplicados e divergentes em vários arquivos, alguns com `name` (errado) em vez de `full_name` (campo real retornado pelo backend).

Corrigidos:
- `src/store/authStore.ts` — `AuthUser.name` trocado para `AuthUser.full_name`
- `src/api/auth.ts` — `MeResponse.name` trocado para `MeResponse.full_name` (linha 16)
- `src/components/layout/Sidebar.tsx` — `user?.name` trocado para `user?.full_name` (2 ocorrências: cálculo de `initials` e texto exibido no rodapé)

Confirmado como correto / falso positivo (campo `name` é o certo para essas entidades, não confundir com o bug):
- `src/api/customers.ts:5` — Customer usa `name`
- `src/hooks/useCompany.ts:6` — Company usa `name`
- `src/hooks/useCustomers.ts:6,21` — Customer usa `name`
- `src/hooks/useUsers.ts:8,16` — já usava `full_name` corretamente
- `NewUserForm` (dentro de UsersPage) — já usava `full_name` corretamente em todo o componente

Verificado via teste E2E, mas vale re-observar no futuro:
- `src/pages/OrdersPage.tsx:86` — `options: { id: string; name: string }[]` no dropdown de atribuição de técnico. Passou no teste manual (nomes aparecem certos), mas não houve acesso ao código-fonte completo dessa linha para confirmar 100% a origem do `name` — se algum técnico aparecer sem nome no dropdown futuramente, checar aqui primeiro.

Testes E2E realizados e aprovados na sessão 2B.2:
1. Login sem F5 → nome e iniciais aparecem corretos na Sidebar imediatamente
2. Verificação do objeto `user` no estado do authStore → `full_name` presente e correto
3. F5 após login → nome permanece correto (sem regressão de hidratação)
4. Dropdown de técnico no OrdersPage → nomes aparecem corretos
5. Edição de perfil (SettingsPage) → salva e persiste `full_name` corretamente

## Skeleton Loading — Implementado e validado (sessão 2B.3)

**Componentes criados:**
- `src/components/ui/table-skeleton.tsx` — componente reutilizável `<TableSkeleton rows={N} columns={N} />`, usado em páginas com componentes shadcn `<Table>`. Retorna seu próprio `<TableBody>` internamente — nunca aninhar dentro de outro `<TableBody>`.
- `OrdersPage.tsx` não usa `TableSkeleton` (ver nota estrutural acima) — usa o componente `Skeleton` do shadcn diretamente dentro de um `<table>` HTML pura com `<thead>` real e 8 linhas × 7 colunas de barras animadas.

**Padrão aplicado por página:**
- `UsersPage.tsx`: `{isLoading ? <TableSkeleton rows={5} columns={columnCount} /> : <TableBody>{...}</TableBody>}`, onde `columnCount = isOwner ? 5 : 4`
- `CustomersPage.tsx`: mesmo padrão, com 3 estados (`isLoading` → skeleton; `customers.length === 0` → empty state; senão → dados), `columns={isAdmin ? 5 : 4}`
- `OrdersPage.tsx`: `<table>` de skeleton com cabeçalho real (Nº, Título, Cliente, Técnico, Prioridade, Status, Data); import `Skeleton` de `@/components/ui/skeleton`

**Validação realizada:**
- Skeleton confirmado renderizando corretamente via vídeo de teste na tela de Usuários (barras animadas visíveis antes dos dados reais aparecerem)
- CustomersPage e OrdersPage com código revisado linha a linha, estruturalmente equivalentes ao padrão validado
- Prints de rede (Network tab, throttle Slow 4G) confirmam carregamento bem-sucedido sem erros de console em Users e Orders
- Metodologia de teste validada: throttle "Slow 4G" no DevTools é suficiente e mais previsível que "3G"
- Para testes futuros de loading state: ativar o throttle **depois** que o app já montou, ou usar "Screenshots" do painel Network

## Empty States — Implementado e validado (sessão 2B.4)

**Padrão aplicado (título + descrição + botão condicional por permissão):**
- `OrdersPage.tsx` — já existia desde a criação da tela; mensagem contextual (filtro ativo vs sem OS) + botão "Criar OS →"; botão oculto quando há filtro de status ativo (o problema é o filtro, não a ausência de dados)
- `CustomersPage.tsx` — mensagem contextual já existia (busca vs cadastro vazio); adicionado botão "Novo Cliente" via `openCreate`, visível apenas quando `isAdmin && !search`
- `UsersPage.tsx` — criado do zero: `TableBody` reestruturado com ternário `users.length === 0 ? (empty state) : users.map(...)`; botão "Novo Usuário" visível apenas quando `isAdmin`; usa `colSpan={columnCount}`

**Testes realizados:**
- CustomersPage e OrdersPage: validado via busca/filtro sem resultados (cenário real)
- UsersPage: validado via mock temporário (`const users: AppUser[] = []`) — confirmado visualmente que mensagem e botão aparecem para admin/owner; reversão do mock confirmada antes de prosseguir
- Pendente (não bloqueante): testar UsersPage com um usuário técnico logado, para confirmar que o botão "Novo Usuário" some corretamente nesse caso

## Limpeza de Debug (sessão 2B.4)
- Removidos os 3 `console.log` de debug em `OrdersPage.tsx`:
  - `CustomSelect`: `console.log('CustomSelect options:', options)`
  - `CreateOrderModal`: `console.log('items:', usersData?.items)`
  - `CreateOrderModal`: `console.log('technicians após filtro:', technicians)`
- Recomendado (não executado ainda): rodar busca `Select-String -Path "src\**\*.tsx" -Pattern "console.log" -Recurse` para confirmar que não restam outros logs esquecidos no projeto

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
- Free: R$ 0/mês
- Básico: R$ 67/mês
- Pro: R$ 127/mês
- Empresa: R$ 247/mês

## Estrutura de Pastas (estado atual)

serviceflow/
├── .venv/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── router.py                          OK
│   │   │   └── endpoints/
│   │   │       ├── auth.py                        OK
│   │   │       ├── companies.py                   OK
│   │   │       ├── users.py                       OK
│   │   │       ├── customers.py                   OK
│   │   │       └── service_orders.py              OK
│   │   ├── core/
│   │   │   ├── config.py                          OK
│   │   │   ├── security.py                        OK
│   │   │   ├── dependencies.py                    OK
│   │   │   └── exceptions.py                      OK
│   │   ├── db/
│   │   │   ├── session.py                         OK
│   │   │   └── base.py                            OK
│   │   ├── models/                                OK
│   │   ├── repositories/                          OK
│   │   ├── schemas/                                OK
│   │   ├── services/                               OK
│   │   └── main.py                                 OK
│   ├── tests/                                      OK
│   │   ├── conftest.py                             OK
│   │   ├── test_auth.py                            OK
│   │   ├── test_companies.py                       OK
│   │   ├── test_users.py                           OK
│   │   ├── test_customers.py                       OK
│   │   └── test_service_orders.py                  OK
│   ├── alembic/versions/
│   │   ├── 06d5ab8065eb_initial_schema.py          OK
│   │   └── xxxx_expand_customer_address_fields.py  OK
│   ├── .env
│   ├── .env.example
│   ├── .env.test                                   OK
│   ├── pytest.ini                                  OK
│   ├── alembic.ini
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements.lock
└── frontend/                                       OK
    ├── src/
    │   ├── api/
    │   │   ├── client.ts                           OK (axios + interceptor JWT)
    │   │   ├── auth.ts                             OK (full_name corrigido)
    │   │   ├── customers.ts                        OK
    │   │   ├── orders.ts                           OK (create, update, delete adicionados)
    │   │   └── users.ts                             OK
    │   ├── components/
    │   │   ├── layout/
    │   │   │   ├── AppLayout.tsx                   OK
    │   │   │   └── Sidebar.tsx                     OK (full_name corrigido; Header.tsx não existe, funcionalidade está aqui)
    │   │   └── ui/                                  OK (shadcn/ui components)
    │   │       └── table-skeleton.tsx               OK (componente reutilizável de skeleton)
    │   ├── hooks/
    │   │   ├── useAuth.ts                          VAZIO — código morto, não importado em lugar nenhum
    │   │   ├── useCompany.ts                       OK
    │   │   ├── useCustomers.ts                     OK
    │   │   ├── useOrders.ts                        OK
    │   │   └── useUsers.ts                          OK (full_name correto)
    │   ├── pages/
    │   │   ├── LoginPage.tsx                       OK
    │   │   ├── DashboardPage.tsx                   OK
    │   │   ├── OrdersPage.tsx                      OK (skeleton loading, empty state e console.log de debug removidos; tabela HTML pura, não shadcn — dívida técnica)
    │   │   ├── OrderDetailPage.tsx                 OK
    │   │   ├── CustomersPage.tsx                   OK (skeleton loading + empty state com botão de ação, ambos validados)
    │   │   ├── UsersPage.tsx                       OK (skeleton loading + empty state com botão de ação, ambos validados)
    │   │   └── SettingsPage.tsx                    OK (form de perfil testado, salva full_name corretamente)
    │   ├── router/
    │   │   └── index.tsx                           OK (ProtectedRoute via accessToken, reativo, sem bugs)
    │   ├── store/
    │   │   └── authStore.ts                        OK (full_name corrigido)
    │   ├── types/
    │   │   └── api.ts                              VAZIO — gerar via openapi-typescript antes do deploy (Fase 3, prioridade alta)
    │   └── main.tsx                                 OK (Toaster montado)
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
| POST | /api/v1/auth/register | Público |
| POST | /api/v1/auth/login | Público |
| POST | /api/v1/auth/refresh | Público |
| GET | /api/v1/auth/me | Bearer |

### Companies
| Método | Rota | Auth |
|--------|------|------|
| GET | /api/v1/companies/me | CurrentUser |
| PATCH | /api/v1/companies/me | OwnerOnly |

### Users
| Método | Rota | Auth |
|--------|------|------|
| GET | /api/v1/users | AdminOnly |
| POST | /api/v1/users | AdminOnly |
| GET | /api/v1/users/me | CurrentUser |
| GET | /api/v1/users/{id} | AdminOnly |
| PATCH | /api/v1/users/{id} | CurrentUser |
| DELETE | /api/v1/users/{id} | OwnerOnly |
| PATCH | /api/v1/users/{id}/role | OwnerOnly |

### Customers
| Método | Rota | Auth |
|--------|------|------|
| GET | /api/v1/customers | TechOrAbove |
| POST | /api/v1/customers | AdminOnly |
| GET | /api/v1/customers/{id} | TechOrAbove |
| PATCH | /api/v1/customers/{id} | AdminOnly |
| DELETE | /api/v1/customers/{id} | AdminOnly |

### Service Orders
| Método | Rota | Auth |
|--------|------|------|
| GET | /api/v1/orders | TechOrAbove |
| POST | /api/v1/orders | AdminOnly |
| GET | /api/v1/orders/{id} | TechOrAbove |
| PATCH | /api/v1/orders/{id} | TechOrAbove |
| DELETE | /api/v1/orders/{id} | AdminOnly |
| PATCH | /api/v1/orders/{id}/status | TechOrAbove |
| GET | /api/v1/orders/{id}/items | TechOrAbove |
| POST | /api/v1/orders/{id}/items | TechOrAbove |
| DELETE | /api/v1/orders/{id}/items/{item_id} | TechOrAbove |

## Fase 2A — Concluída
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
- Sonner montado no main.tsx

## Fase 2B — Concluída
- [x] Formulário de criação de OS na OrdersPage com modal + react-hook-form + zod
- [x] Validação de formulários com react-hook-form + zod
- [x] Confirmar que todas as telas funcionam com backend rodando (validação E2E completa)
- [x] CustomSelect para contornar limitação do Chrome com option estilizado
- [x] Guard de permissão por role em botões e campos do formulário
- [x] Correção enum priority: normal em vez de medium
- [x] Correção campo usuário: full_name em vez de name
- [x] Correção validator documento cliente: aceitar string vazia como None
- [x] authStore atualiza user corretamente após login, sem F5 (sessão 2B.2)
- [x] Skeleton loading nas tabelas — 3 páginas (Users, Customers, Orders) (sessão 2B.3)
- [x] Empty states com botão de ação direto — 3 páginas (sessão 2B.4)
- [x] Remover os 3 console.log de debug em CreateOrderModal (OrdersPage.tsx) (sessão 2B.4)

## Fase 3 — Preparação para Deploy (em andamento)
- [ ] Gerar `types/api.ts` via `openapi-typescript` a partir de `/openapi.json` — prioridade alta, elimina a causa raiz da cadeia de bugs name/full_name antes de ir para produção
- [ ] Decidir sobre `hooks/useAuth.ts` vazio — remover ou implementar como wrapper de `useAuthStore`
- [ ] `order_number` como `INTEGER` no banco (atual é `VARCHAR`) — migration Alembic
- [ ] `assigned_to` no schema → renomear para `technician_id` para consistência
- [ ] `components.json` — trocar `"style": "radix-nova"` por `"style": "default"` para evitar bug de instalação de componentes na pasta `@`
- [ ] `tsconfig.app.json` — adicionar `"ignoreDeprecations": "6.0"` para silenciar warning do baseUrl
- [ ] Variáveis de ambiente de produção — backend (Hetzner) e frontend (Vercel): `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, URL da API pública
- [ ] Configurar CORS no FastAPI para o domínio de produção do frontend (Vercel)
- [ ] Dockerfile de produção do backend — revisar se o `Dockerfile` atual (dev) precisa de ajustes para deploy (multi-stage build, non-root user, etc.)
- [ ] Rodar migrations Alembic em produção (estratégia: manual no primeiro deploy vs. automatizado via CI/CD)
- [ ] Build de produção do frontend (`npm run build`) — validar localmente antes do primeiro deploy no Vercel
- [ ] Decidir sobre HTTPS/domínio próprio (Hetzner VPS geralmente exige configuração manual de reverse proxy — Nginx ou Caddy — + certificado TLS)
- [ ] Rodar suíte de testes pytest (68/68) uma última vez antes do primeiro deploy, como checkpoint de regressão

## Decisões Pendentes / A Revisar (baixa prioridade, pós-deploy)
- [ ] Avaliar soft delete (deleted_at) vs is_active
- [ ] Avaliar RefreshToken model para blacklist
- [ ] Avaliar Checklist/ChecklistItem model (fase futura)
- [ ] Avaliar computed_field no config.py para DATABASE_URL automático
- [ ] Técnico autônomo: documentar no onboarding que deve se cadastrar como owner, sugerindo placeholder "Ex: João Silva Refrigeração" no campo empresa
- [ ] Considerar refatorar `OrdersPage.tsx` para usar componentes shadcn `<Table>` (como Users/Customers) em vez de `<table>` HTML pura com estilos inline — dívida técnica de consistência, não bloqueante para deploy
- [ ] Rodar `Select-String -Path "src\**\*.tsx" -Pattern "console.log" -Recurse` para confirmar ausência de outros logs de debug esquecidos no projeto
- [ ] Testar UsersPage com usuário técnico logado, para confirmar que botão "Novo Usuário" some corretamente (empty state)