# ServiceFlow — Project Continuity Document

## Sessão Atual
**Fase:** 1E — CRUD Base + Service Layer
**Status:** Aguardando

## Progresso das Fases

| Fase | Descrição | Status |
|------|-----------|--------|
| 1A | Estrutura base + Docker + Config | ✅ Concluída |
| 1B | Models SQLAlchemy 2.0 + Alembic | ✅ Concluída |
| 1C | Schemas Pydantic v2 | ✅ Concluída |
| 1D | Auth JWT (login, refresh, dependency) | ✅ Concluída |
| 1E | CRUD Base + Service Layer | ⏳ Próxima |
| 1F | Endpoints REST /api/v1 | ⏳ Pendente |

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
- `email-validator>=2.0.0` adicionado ao requirements.txt (dependência opcional do Pydantic v2 para EmailStr)
- Schemas em `backend/app/schemas/` com padrão Base/Create/Update/Response por entidade
- `PaginatedResponse[T]` genérico para todas as listagens
- `ServiceOrderSummary` para dashboards (evita trafegar campos grandes)
- `ServiceOrderStatusUpdate` em endpoint separado (PATCH /orders/{id}/status)
- `bcrypt==4.0.1` pinado (última versão compatível com passlib)
- Enums com nomes UPPERCASE no Python (`UserRole.OWNER`), valores serializados em lowercase (`"owner"`)
- `role` mapeado como `String` no banco — ao criar User, passar `owner.role` diretamente (não `.value`)
- Slug de Company gerado como `slugify(name)-uuid[:8]` para garantir unicidade
- `_slugify()` usando `unicodedata.normalize NFKD` para remover acentos
- Auth implementado em `app/core/security.py` + `app/core/dependencies.py` + `app/services/auth_service.py`
- `CurrentUser`, `AdminOnly`, `OwnerOnly`, `TechOrAbove` como atalhos de dependency no `dependencies.py`
- Registro cria Company + User(OWNER) + Subscription(TRIALING 14 dias) em transação única com `flush()`
- Refresh token sem blacklist no MVP (decisão pendente para produção)
- `get_db` é o nome da função de sessão em `app/db/session.py` (não `get_session`)
- Todos os comandos devem ser executados de dentro de `backend/` (não da raiz do projeto)

## Stack Técnica
- **Backend:** FastAPI + Python 3.14
- **ORM:** SQLAlchemy 2.0 (DeclarativeBase, Mapped, mapped_column)
- **Banco:** PostgreSQL 16 Alpine via Docker
- **Migrations:** Alembic 1.18.4
- **Validação:** Pydantic v2 + pydantic-settings
- **Auth:** python-jose + passlib + bcrypt==4.0.1
- **Driver async:** asyncpg 0.31.0
- **Venv:** .venv em serviceflow/ (raiz do projeto)

## Planos e Preços
- **Free:** R$ 0/mês
- **Básico:** R$ 67/mês
- **Pro:** R$ 127/mês
- **Empresa:** R$ 247/mês

## Estrutura de Pastas (estado atual)
```
serviceflow/
├── .venv/                          ← venv na raiz (não no backend/)
└── backend/                        ← ⚠️ todos os comandos rodam daqui
    ├── app/
    │   ├── api/v1/endpoints/
    │   │   └── auth.py             ✅ register, login, refresh, me
    │   ├── core/
    │   │   ├── config.py           ✅ pydantic-settings
    │   │   ├── security.py         ✅ JWT + bcrypt
    │   │   └── dependencies.py     ✅ get_current_user + RBAC guards
    │   ├── db/
    │   │   ├── session.py          ✅ get_db (não get_session)
    │   │   └── base.py
    │   ├── models/                 ✅ COMPLETO
    │   │   ├── __init__.py         ← importa tudo (ponto central)
    │   │   ├── base.py             ← Base, UUIDMixin, TimestampMixin
    │   │   ├── company.py          ← tenant raiz + PlanTier enum
    │   │   ├── user.py             ← auth + UserRole RBAC
    │   │   ├── customer.py         ← cliente do tenant
    │   │   ├── service_order.py    ← OS + ServiceItem + enums
    │   │   └── subscription.py     ← controle de plano SaaS
    │   ├── schemas/                ✅ COMPLETO
    │   │   ├── __init__.py
    │   │   ├── common.py           ← BaseSchema, PaginatedResponse, MessageResponse
    │   │   ├── company.py
    │   │   ├── user.py             ← usa full_name (não name)
    │   │   ├── customer.py
    │   │   ├── service_item.py
    │   │   ├── service_order.py
    │   │   └── subscription.py
    │   ├── services/               ✅ auth concluído
    │   │   └── auth_service.py     ← register, login, refresh_tokens
    │   └── main.py
    ├── alembic/                    ✅ CONFIGURADO
    │   ├── env.py                  ← async, importa Base + settings
    │   ├── script.py.mako
    │   └── versions/
    │       └── 06d5ab8065eb_initial_schema.py  ✅ aplicada
    ├── .env                        ← DATABASE_URL com localhost (local)
    ├── .env.example
    ├── alembic.ini                 ✅ sqlalchemy.url vazio (vem do config)
    ├── docker-compose.yml
    ├── Dockerfile
    ├── requirements.txt
    └── requirements.lock           ← versões reais instaladas
```

## Models Implementados (Fase 1B)

### Tabelas no banco (7)
| Tabela | Model | Descrição |
|--------|-------|-----------|
| companies | Company | Tenant raiz (autônomo ou empresa) |
| users | User | Auth + RBAC (owner/admin/technician/viewer) |
| customers | Customer | Clientes do tenant |
| service_orders | ServiceOrder | Núcleo do FSM — ciclo de vida da OS |
| service_items | ServiceItem | Itens/peças de cada OS |
| subscriptions | Subscription | Controle de plano SaaS por tenant |
| alembic_version | — | Controle de migrations |

### Campos importantes do model User
- `full_name` (não `name`)
- `is_verified` (Boolean, default False)
- `avatar_url` (String opcional)
- `role` mapeado como `String(20)` no banco

### Enums definidos (nomes UPPERCASE, valores lowercase)
- `PlanTier`: FREE / BASICO / PRO / EMPRESA
- `UserRole`: OWNER / ADMIN / TECHNICIAN / VIEWER
- `OrderStatus`: DRAFT → SCHEDULED → IN_PROGRESS → COMPLETED → INVOICED / CANCELLED
- `OrderPriority`: LOW / NORMAL / HIGH / URGENT
- `ItemType`: LABOR / PART / TRAVEL / OTHER
- `SubscriptionStatus`: TRIALING / ACTIVE / PAST_DUE / CANCELLED / EXPIRED

## Endpoints Implementados (Fase 1D)

| Método | Rota | Descrição | Auth |
|--------|------|-----------|------|
| POST | `/api/v1/auth/register` | Cria empresa + owner + subscription trial | Público |
| POST | `/api/v1/auth/login` | Login com e-mail e senha | Público |
| POST | `/api/v1/auth/refresh` | Renova tokens (rotation) | Público |
| GET | `/api/v1/auth/me` | Dados do usuário autenticado | Bearer |

## RBAC — Guards disponíveis (dependencies.py)
```python
CurrentUser   # qualquer usuário autenticado
AdminOnly     # OWNER + ADMIN
OwnerOnly     # OWNER apenas
TechOrAbove   # OWNER + ADMIN + TECHNICIAN
```

## Comandos Úteis

```powershell
# ⚠️ Sempre rodar de dentro de backend/
cd backend

# Banco
docker compose up -d db
docker compose exec db psql -U serviceflow -d serviceflow_db -c "\dt"
docker compose exec db psql -U serviceflow -d serviceflow_db -c "SELECT id, full_name, email, role FROM users;"
docker compose exec db psql -U serviceflow -d serviceflow_db -c "SELECT id, name, slug, plan_tier FROM companies;"

# Migrations
python -m alembic revision --autogenerate -m "descricao"
python -m alembic upgrade head
python -m alembic downgrade -1

# App
uvicorn app.main:app --reload
docker compose logs -f api

# Swagger
# http://localhost:8000/docs
```

## Startup do Zero (após reiniciar o PC)
```powershell
# 1. Abrir Docker Desktop e aguardar baleia verde
# 2. Entrar na pasta correta
cd C:\Users\junio\Documents\Projetos\serviceflow\backend
# 3. Ativar venv
..\.venv\Scripts\Activate.ps1
# 4. Subir banco
docker compose up -d db
# 5. Rodar API
uvicorn app.main:app --reload
# 6. Acessar http://localhost:8000/docs
```

## Variáveis de Ambiente (.env local)
```env
# ATENÇÃO: DATABASE_URL usa localhost para rodar alembic/app fora do Docker
# Dentro do Docker, o host é "db" (nome do serviço)
DATABASE_URL=postgresql+asyncpg://serviceflow:senha@localhost:5432/serviceflow_db
POSTGRES_HOST=localhost

# JWT — gerar SECRET_KEY com: openssl rand -hex 32
SECRET_KEY=sua_chave_aqui
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Decisões Pendentes / A Revisar
- [ ] Avaliar `computed_field` no config.py para gerar DATABASE_URL automaticamente
- [ ] Avaliar soft delete (`deleted_at`) vs `is_active` para auditoria
- [ ] Avaliar `RefreshToken` model separado para revogar tokens individuais (blacklist)
- [ ] Avaliar `Checklist/ChecklistItem` model (checklist de campo — fase 2)
- [ ] Definir estratégia de geração do `order_number` (ex: OS-2025-00042)