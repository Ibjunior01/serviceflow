# ServiceFlow

> SaaS B2B de Field Service Management para técnicos autônomos e pequenas empresas de refrigeração e ar-condicionado.

🟢 **Aplicação em produção:** https://serviceflow-liard.vercel.app
📘 **API / Swagger:** https://serviceflow-backend-5ljk.onrender.com/docs

---

## Sobre o projeto

O ServiceFlow é uma aplicação Full Stack para gestão de operações de campo e ordens de serviço.

O case foi desenvolvido com foco em:

- arquitetura SaaS multi-tenant;
- autenticação JWT e autorização por perfil;
- gestão de clientes, usuários, técnicos e ordens de serviço;
- máquina de estados de ordens;
- planos, trial e limites de utilização;
- dashboard com agregações no backend;
- migrations versionadas;
- testes automatizados;
- hardening de segurança;
- CI com GitHub Actions;
- deploy separado de frontend, backend e banco de dados.

A arquitetura atual é um **monólito modular**, adequada ao porte e ao estágio do produto.

---

## Stack técnica

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI + Python 3.14 |
| ORM | SQLAlchemy 2 assíncrono |
| Banco | PostgreSQL |
| Driver | asyncpg |
| Migrations | Alembic |
| Validação | Pydantic v2 |
| Autenticação | JWT access + refresh |
| Testes | pytest + pytest-asyncio + httpx |
| Frontend | React 19 + TypeScript + Vite |
| UI | Tailwind CSS + shadcn/ui |
| Estado | Zustand |
| Data fetching | TanStack Query |
| Formulários | React Hook Form + Zod |
| HTTP client | Axios |
| Gráficos | Recharts |
| Frontend produção | Vercel |
| Backend produção | Render |
| PostgreSQL produção | Neon |
| CI | GitHub Actions |

---

## Arquitetura

```text
React / TypeScript
        ↓
Axios + TanStack Query
        ↓
REST API FastAPI
        ↓
Services
        ↓
Repositories
        ↓
SQLAlchemy Async
        ↓
PostgreSQL
```

### Decisões de arquitetura

| Decisão | Motivo |
|---|---|
| Monólito modular | Menor complexidade operacional sem perder separação de responsabilidades |
| FastAPI | API tipada, assíncrona e OpenAPI automático |
| SQLAlchemy async | Persistência assíncrona com PostgreSQL |
| PostgreSQL | Integridade relacional e constraints transacionais |
| Alembic | Evolução versionada do schema |
| API `/api/v1` | Versionamento do contrato HTTP |
| Services + Repositories | Separação entre regras de negócio e persistência |
| TanStack Query | Cache e sincronização de estado remoto |
| Zustand | Estado local compartilhado |
| Constraint `(company_id, order_number)` | Numeração de OS independente por tenant |
| FSM de status | Bloqueio de transições inválidas |

---

## Funcionalidades implementadas

- registro público de novas empresas;
- autenticação com access e refresh token;
- multi-tenancy por empresa;
- usuários e técnicos;
- clientes;
- ordens de serviço;
- atribuição de técnico;
- prioridades e agendamento;
- itens, peças e serviços;
- máquina de estados das ordens;
- planos e trial;
- limites do plano FREE;
- dashboard operacional agregado no backend;
- API REST versionada;
- OpenAPI / Swagger;
- migrations Alembic;
- testes automatizados;
- headers de segurança e CSP bloqueante;
- code splitting no frontend;
- CI automatizado;
- deploy em produção.

### Estado funcional

```text
Backend FastAPI                 IMPLEMENTADO
Frontend React                  IMPLEMENTADO
PostgreSQL                      IMPLEMENTADO
Alembic                         IMPLEMENTADO
JWT                             IMPLEMENTADO
RBAC OWNER/ADMIN/TECHNICIAN     IMPLEMENTADO
RBAC VIEWER                     PARCIAL
Multi-tenancy                   IMPLEMENTADO
FSM de Ordens                   IMPLEMENTADO
Trial PRO                       IMPLEMENTADO
Downgrade FREE                  IMPLEMENTADO
Limites FREE                    IMPLEMENTADO
Dashboard agregado              IMPLEMENTADO
Deploy                          IMPLEMENTADO
CI                              IMPLEMENTADO
Revogação server-side JWT       ROADMAP
```

---

## Multi-tenancy

`company_id` é a chave de isolamento entre tenants.

Há cobertura automatizada de isolamento para recursos relevantes, incluindo clientes, usuários, ordens e dashboard.

### Numeração das ordens

A unicidade da OS é:

```text
(company_id, order_number)
```

Portanto:

```text
Empresa A → OS 1
Empresa A → OS 2

Empresa B → OS 1
Empresa B → OS 2
```

A geração atual usa `MAX(order_number) + 1` por empresa. A constraint do banco protege a integridade, mas a estratégia possui risco de colisão sob concorrência simultânea e permanece no roadmap de hardening.

---

## RBAC

Perfis modelados:

```text
OWNER
ADMIN
TECHNICIAN
VIEWER
```

Para ordens de serviço:

```text
OWNER / ADMIN → todas as OS do tenant
TECHNICIAN    → apenas OS atribuídas a ele
```

O escopo do `TECHNICIAN` é aplicado em listagem, detalhe, atualização, mudança de status e operações de itens. O técnico não pode reatribuir sua própria OS para outro técnico.

O perfil `VIEWER` existe no domínio, mas sua política funcional específica ainda não foi formalizada integralmente; por isso permanece **parcialmente implementado**.

---

## Máquina de estados da OS

```text
DRAFT
 ├─→ SCHEDULED
 └─→ CANCELLED

SCHEDULED
 ├─→ IN_PROGRESS
 └─→ CANCELLED

IN_PROGRESS
 ├─→ COMPLETED
 └─→ CANCELLED

COMPLETED
 └─→ INVOICED

INVOICED  → terminal
CANCELLED → terminal
```

Transições fora desse fluxo são rejeitadas pela camada de serviço.

---

## Planos e trial

| Plano | Preço definido |
|---|---:|
| Free | R$ 0/mês |
| Básico | R$ 67/mês |
| Pro | R$ 127/mês |
| Empresa | R$ 247/mês |

Novas empresas iniciam em `PRO / TRIALING` por aproximadamente 14 dias.

Após o vencimento, o downgrade para `FREE / ACTIVE` ocorre de forma lazy/on-request.

### Limites FREE

| Recurso | Limite |
|---|---:|
| Técnicos | 1 |
| Clientes | 5 |
| Ordens de serviço | 10 por mês |

---

## Dashboard

O dashboard não depende mais de uma listagem limitada a 50 ordens.

O frontend utiliza:

```text
GET /api/v1/dashboard/summary
```

O backend calcula:

- contagens por status;
- ordens por mês nos últimos seis meses;
- oito ordens recentes.

O endpoint respeita o RBAC:

```text
OWNER / ADMIN → dados do tenant
TECHNICIAN    → apenas ordens atribuídas ao técnico
```

Há testes para volume superior a 50 ordens, dashboard vazio, isolamento entre tenants e escopo `TECHNICIAN`.

---

## Segurança e hardening

Controles presentes:

- hashing de senha;
- JWT;
- separação entre access e refresh token;
- validação de usuário e empresa ativos;
- RBAC;
- isolamento multi-tenant;
- rate limiting em runtime;
- CORS por ambiente;
- validação Pydantic;
- headers HTTP de segurança;
- CSP bloqueante sem `unsafe-eval`;
- Zod em modo `jitless`;
- tratamento da fila concorrente de refresh;
- auditoria de dependências;
- revisão de credenciais versionadas.

### Headers validados

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Strict-Transport-Security
Content-Security-Policy
```

### Limitação conhecida de sessão

Os tokens permanecem no `localStorage`.

Não há atualmente blacklist, `jti` persistido, token family ou revogação server-side. O logout remove os tokens no cliente.

Para o escopo de MVP/portfólio essa limitação está documentada. Antes de cenários comerciais mais sensíveis, a arquitetura de sessão deve ser revista em conjunto, incluindo revogação server-side, cookie `HttpOnly`, CSRF e logout efetivo.

---

## Testes e qualidade

### Backend

Validação atual:

```text
pytest -q
90 passed, 2 warnings

python -m pip check
No broken requirements found.
```

Os dois warnings restantes são originados no SlowAPI sob Python 3.14.

A suíte cobre, entre outros pontos:

- autenticação;
- access e refresh token;
- usuário e empresa inativos;
- RBAC;
- multi-tenancy;
- ordens;
- FSM;
- escopo de `TECHNICIAN`;
- numeração por empresa;
- trial e downgrade;
- limites FREE;
- dashboard agregado.

### Frontend

```text
npx --no-install tsc --noEmit   OK
npm run build                   OK
npm audit                       0 vulnerabilities
npm audit --omit=dev            0 vulnerabilities
```

Foi implementado code splitting por rota.

Build validado:

```text
Bundle principal antes   ~1.060,76 kB
Bundle principal depois  ~351,61 kB
gzip principal           ~109,32 kB
DashboardPage            ~357,73 kB
chunks > 500 kB          nenhum
```

---

## CI — GitHub Actions

O repositório possui pipeline em:

```text
.github/workflows/ci.yml
```

Em `push` e `pull_request` para `main`, o CI executa dois jobs independentes.

### Backend

```text
PostgreSQL 16 descartável
Python 3.14
pip install -r requirements.lock
pip check
Alembic upgrade head
pytest -q
```

### Frontend

```text
Node 24
npm ci
TypeScript check
Vite build
npm audit
npm audit --omit=dev
```

Última execução validada:

```text
Backend   ✅
Frontend  ✅
```

O pipeline não acessa o banco Neon de produção.

---

## Como executar localmente

### Pré-requisitos

- Python 3.14;
- PostgreSQL;
- Node.js 24 recomendado;
- npm;
- Git.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
python -m alembic upgrade head
uvicorn app.main:app --reload
```

Swagger:

```text
http://localhost:8000/docs
```

### Frontend

Em outro terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Aplicação:

```text
http://localhost:5173
```

### Testes

O banco de testes deve ser independente do banco de desenvolvimento e de produção.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

---

## Variáveis de ambiente

Nunca versione credenciais reais.

Exemplo de backend:

```env
APP_NAME=ServiceFlow
APP_ENV=development

DATABASE_URL=postgresql+asyncpg://<usuario>:<senha>@localhost:5432/<banco>

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=<usuario>
POSTGRES_PASSWORD=<senha>
POSTGRES_DB=<banco>

SECRET_KEY=<segredo-exclusivo-do-ambiente>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=http://localhost:5173
```

Frontend:

```env
VITE_API_URL=http://localhost:8000
```

Em produção, as variáveis reais são configuradas diretamente no provedor e não ficam no Git.

---

## Deploy

```text
Vercel
React / Vite
     │
     │ HTTPS / REST
     ▼
Render
FastAPI
     │
     │ SQLAlchemy + asyncpg
     ▼
Neon
PostgreSQL
```

### Frontend

- Vercel;
- root directory: `frontend`;
- framework: Vite.

### Backend

- Render;
- container: `backend/Dockerfile.prod`;
- health check: `/health`;
- branch de deploy: `main`.

### Banco

- Neon PostgreSQL;
- schema controlado por Alembic;
- revisão validada: `3e89efe30105`.

---

## Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/auth/register` | Cria tenant, owner e subscription |
| POST | `/api/v1/auth/login` | Autenticação |
| POST | `/api/v1/auth/refresh` | Renova tokens |
| GET | `/api/v1/auth/me` | Usuário autenticado |
| GET/POST | `/api/v1/customers` | Clientes |
| GET/POST | `/api/v1/orders` | Ordens de serviço |
| GET | `/api/v1/orders/{id}` | Detalhe da OS |
| PATCH | `/api/v1/orders/{id}` | Atualização da OS |
| PATCH | `/api/v1/orders/{id}/status` | Transição da FSM |
| GET/POST | `/api/v1/orders/{id}/items` | Itens |
| DELETE | `/api/v1/orders/{id}/items/{item_id}` | Remove item |
| GET | `/api/v1/dashboard/summary` | Agregações do dashboard |
| GET | `/health` | Health check |

---

## Limitações conhecidas / roadmap

- formalizar a política do `VIEWER`;
- endurecer a geração concorrente de `order_number`;
- revisar campos de schema de OS ainda sem persistência equivalente;
- revisar `technician_notes` e criação de OS com `items`;
- avaliar revogação server-side e arquitetura de sessão;
- reduzir `style-src 'unsafe-inline'`;
- acompanhar compatibilidade do SlowAPI com Python 3.14;
- realizar auditoria específica de acessibilidade;
- otimizar bundle adicionalmente apenas se métricas reais justificarem.

---

## Estado atual

```text
Produção          ✅
Multi-tenancy     ✅
RBAC principal    ✅
FSM               ✅
Planos / trial    ✅
Dashboard backend ✅
90 testes         ✅
CI                ✅
CSP bloqueante    ✅
npm audit         ✅ 0 vulnerabilidades
```

O ServiceFlow está na **ETAPA 11 — revisão final para portfólio**. As funcionalidades não concluídas permanecem explicitamente separadas como limitações ou roadmap.
