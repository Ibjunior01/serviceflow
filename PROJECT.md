# ServiceFlow — Project Continuity Document

## Sessão Atual
**Fase:** 1G — Testes Automatizados (pytest + httpx)
**Status:** Aguardando início

## Progresso das Fases

| Fase | Descrição | Status |
|------|-----------|--------|
| 1A | Estrutura base + Docker + Config | ✅ Concluída |
| 1B | Models SQLAlchemy 2.0 + Alembic | ✅ Concluída |
| 1C | Schemas Pydantic v2 | ✅ Concluída |
| 1D | Auth JWT (login, refresh, dependency) | ✅ Concluída |
| 1E | CRUD Base + Service Layer | ✅ Concluída |
| 1F | Endpoints REST /api/v1 | ✅ Concluída |
| 1G | Testes Automatizados pytest + httpx | ⏳ Próxima |
| 2A | Frontend React + Vite + Tailwind | 🔜 Futura |

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

## Planos e Preços
- **Free:** R$ 0/mês
- **Básico:** R$ 67/mês
- **Pro:** R$ 127/mês
- **Empresa:** R$ 247/mês

## Estrutura de Pastas (estado atual)
serviceflow/

├── .venv/

└── backend/

├── app/

│   ├── api/v1/

│   │   ├── router.py           ✅

│   │   └── endpoints/

│   │       ├── auth.py         ✅

│   │       ├── companies.py    ✅

│   │       ├── users.py        ✅

│   │       ├── customers.py    ✅

│   │       └── service_orders.py ✅

│   ├── core/

│   │   ├── config.py           ✅

│   │   ├── security.py         ✅

│   │   ├── dependencies.py     ✅

│   │   └── exceptions.py       ✅

│   ├── db/

│   │   ├── session.py          ✅

│   │   └── base.py

│   ├── models/                 ✅

│   ├── repositories/           ✅

│   ├── schemas/                ✅

│   ├── services/               ✅

│   └── main.py                 ✅

├── tests/                      ⏳ a criar

│   ├── conftest.py             ← fixtures globais (db, client, usuários)

│   ├── test_auth.py            ← register, login, refresh, me

│   ├── test_companies.py       ← GET/PATCH /me

│   ├── test_users.py           ← CRUD + role + guards RBAC

│   ├── test_customers.py       ← CRUD + isolamento tenant

│   └── test_service_orders.py  ← CRUD + FSM + items + guards

├── alembic/versions/

│   ├── 06d5ab8065eb_initial_schema.py          ✅

│   └── xxxx_expand_customer_address_fields.py  ✅

├── .env

├── .env.example

├── .env.test                   ⏳ a criar

├── alembic.ini

├── docker-compose.yml

├── Dockerfile

├── requirements.txt

└── requirements.lock

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

## Plano Fase 1G — Testes Automatizados

### Dependências a instalar
pytest==8.3.5

pytest-asyncio==0.24.0

httpx==0.27.0

### Estratégia
- Banco de testes isolado (`serviceflow_test`) no mesmo Docker
- Fixtures criam e destroem dados a cada teste
- `AsyncClient` do httpx aponta para a app FastAPI diretamente (sem servidor real)
- Cada arquivo de teste é independente — sem dependência de ordem

### Casos críticos a cobrir
| Área | Casos |
|------|-------|
| Auth | register, login, token expirado, refresh |
| RBAC | técnico bloqueado em rota AdminOnly, viewer bloqueado |
| FSM | transições válidas, transições inválidas, terminal |
| Guards | editar OS finalizada, deletar não-DRAFT |
| Tenant | usuário de empresa A não acessa dados de empresa B |

## Decisões Pendentes / A Revisar
- [ ] `order_number` como `INTEGER` no banco (atual é VARCHAR)
- [ ] `assigned_to` no schema → renomear para `technician_id` para consistência
- [ ] Avaliar soft delete (`deleted_at`) vs `is_active`
- [ ] Avaliar `RefreshToken` model para blacklist
- [ ] Avaliar `Checklist/ChecklistItem` model (fase 2)
- [ ] Avaliar `computed_field` no config.py para DATABASE_URL automático