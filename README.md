# ServiceFlow

> Field Service Management para técnicos de refrigeração e ar-condicionado no Brasil.

---

## Sumário

- [Sobre o Projeto](#sobre-o-projeto)
- [Stack Técnica](#stack-técnica)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Pré-requisitos](#pré-requisitos)
- [Startup — Passo a Passo](#startup--passo-a-passo)
- [Comandos Úteis](#comandos-úteis)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Arquitetura e Decisões Técnicas](#arquitetura-e-decisões-técnicas)
- [Planos e Preços](#planos-e-preços)
- [Progresso das Fases](#progresso-das-fases)
- [Decisões Pendentes](#decisões-pendentes)

---

## Sobre o Projeto

ServiceFlow é um SaaS de gestão de ordens de serviço (OS) voltado para técnicos autônomos e pequenas empresas de refrigeração e ar-condicionado. Permite abertura, agendamento, execução e faturamento de OS com controle de equipe e histórico do cliente.

---

## Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI + Python 3.14 |
| ORM | SQLAlchemy 2.0 (async) |
| Banco | PostgreSQL 16 Alpine (Docker) |
| Migrations | Alembic 1.18.4 |
| Validação | Pydantic v2 + pydantic-settings |
| Auth | python-jose + passlib + bcrypt==4.0.1 |
| Driver async | asyncpg 0.31.0 |
| Ambiente | Docker Compose + WSL2 + Windows |
| Testes | pytest + pytest-asyncio + httpx |
| Frontend (2A) | React 18 + Vite + TypeScript + Tailwind + shadcn/ui |

---

## Estrutura de Pastas

```
serviceflow/
├── .venv/                          ← venv na raiz do projeto
└── backend/                        ← ⚠️ todos os comandos rodam daqui
    ├── app/
    │   ├── api/v1/endpoints/
    │   │   └── auth.py             ✅ register, login, refresh, me
    │   ├── core/
    │   │   ├── config.py           ✅ pydantic-settings
    │   │   ├── security.py         ✅ JWT + bcrypt
    │   │   └── dependencies.py     ✅ get_current_user + RBAC
    │   ├── db/
    │   │   ├── session.py          ✅ async session + get_db
    │   │   └── base.py
    │   ├── models/                 ✅ completo
    │   │   ├── base.py             ← Base, UUIDMixin, TimestampMixin
    │   │   ├── company.py          ← tenant + PlanTier
    │   │   ├── user.py             ← auth + UserRole RBAC
    │   │   ├── customer.py         ← clientes do tenant
    │   │   ├── service_order.py    ← OS + ServiceItem + enums
    │   │   └── subscription.py     ← controle de plano SaaS
    │   ├── schemas/                ✅ completo
    │   │   ├── common.py           ← BaseSchema, PaginatedResponse
    │   │   ├── company.py
    │   │   ├── user.py
    │   │   ├── customer.py
    │   │   ├── service_item.py
    │   │   ├── service_order.py
    │   │   └── subscription.py
    │   ├── services/               ✅ auth concluído
    │   │   └── auth_service.py
    │   └── main.py
    ├── alembic/                    ✅ configurado
    │   └── versions/
    │       └── 06d5ab8065eb_initial_schema.py
    ├── .env                        ← não versionar
    ├── .env.example
    ├── alembic.ini
    ├── docker-compose.yml
    ├── Dockerfile
    └── requirements.txt
```

---

## Pré-requisitos

- Python 3.14+
- Docker Desktop (Windows)
- WSL2 habilitado
- Git

---

## Startup — Passo a Passo

> ⚠️ **Todos os comandos devem ser executados de dentro de `backend/`.**

### 1. Abrir o Docker Desktop

Aguarde a baleia ficar verde na barra de tarefas antes de continuar.

### 2. Entrar na pasta correta e ativar o venv

```powershell
cd C:\Users\<seu-usuario>\Documents\Projetos\serviceflow\backend
..\.venv\Scripts\Activate.ps1
```

### 3. Subir o banco de dados

```powershell
docker compose up -d db
```

### 4. Rodar a API

```powershell
uvicorn app.main:app --reload
```

### 5. Acessar o Swagger

```
http://localhost:8000/docs
```

---

### Script de startup rápido

Salve como `backend/dev.ps1` e rode com `.\dev.ps1`:

```powershell
docker compose up -d db
Start-Sleep -Seconds 2
uvicorn app.main:app --reload
```

---

## Comandos Úteis

```powershell
# ─── Banco ───────────────────────────────────────────
# Subir apenas o banco
docker compose up -d db

# Ver tabelas
docker compose exec db psql -U serviceflow -d serviceflow_db -c "\dt"

# Ver usuários cadastrados
docker compose exec db psql -U serviceflow -d serviceflow_db -c "SELECT id, full_name, email, role FROM users;"

# Ver empresas cadastradas
docker compose exec db psql -U serviceflow -d serviceflow_db -c "SELECT id, name, slug, plan_tier FROM companies;"

# ─── Migrations ──────────────────────────────────────
python -m alembic revision --autogenerate -m "descricao"
python -m alembic upgrade head
python -m alembic downgrade -1

# ─── API ─────────────────────────────────────────────
uvicorn app.main:app --reload

# Ver logs do container da API (quando rodando via Docker)
docker compose logs -f api

# ─── Testes ──────────────────────────────────────────
# Subir banco de testes (primeira vez)
docker exec -it backend-db-1 psql -U serviceflow -d serviceflow_db -c "CREATE DATABASE serviceflow_test;"

# Rodar todos os testes
pytest tests/ -v

# Rodar arquivo específico
pytest tests/test_auth.py -v

# Resumo sem traceback
pytest tests/ --tb=no -q
```

---

## Variáveis de Ambiente

Crie `backend/.env` baseado em `.env.example`:

```env
# Banco — usa localhost para rodar alembic/app fora do Docker
# Dentro do Docker, o host é "db" (nome do serviço)
DATABASE_URL=postgresql+asyncpg://serviceflow:senha@localhost:5432/serviceflow_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=serviceflow
POSTGRES_PASSWORD=senha
POSTGRES_DB=serviceflow_db

# App
APP_ENV=development

# JWT — gerar com: openssl rand -hex 32
SECRET_KEY=sua_chave_secreta_aqui
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

> ⚠️ Nunca versionar o `.env`. Ele está no `.gitignore`.

**Gerar SECRET_KEY:**
```bash
# No WSL ou Git Bash:
openssl rand -hex 32
```

---

## Arquitetura e Decisões Técnicas

| Decisão | Motivo |
|---------|--------|
| Async engine (asyncpg) | Performance sob carga — múltiplos técnicos simultâneos |
| UUID v4 como PK | Gerado pelo Python, sem dependência do banco |
| `lazy="selectin"` em todos os relationships | Obrigatório para SQLAlchemy async |
| `ondelete` explícito em todas as FKs | CASCADE / RESTRICT / SET NULL definidos no model |
| Totais financeiros no service layer | Nunca calculados no banco — facilita auditoria e testes |
| Alembic fora do Docker | Host `localhost` no `.env` local; dentro do Docker usa `db` |
| `python -m alembic` | Evita problemas de PATH no Windows |
| Versionamento `/api/v1` desde o início | Backward compatibility futura |
| `bcrypt==4.0.1` pinado | Última versão compatível com passlib |
| `email-validator>=2.0.0` | Dependência opcional do Pydantic v2 para `EmailStr` |
| Schemas com padrão Base/Create/Update/Response | Separação clara de responsabilidades por camada |
| `PaginatedResponse[T]` genérico | Reutilizável em todas as listagens |
| `ServiceOrderStatusUpdate` em endpoint separado | `PATCH /orders/{id}/status` — status nunca muda junto com outros campos |
| Enums com nomes UPPERCASE | Padrão Python: `UserRole.OWNER`, valor serializado `"owner"` |
| Slug gerado como `slugify(name)-uuid[:8]` | Unicidade garantida mesmo com nomes iguais |


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

### Endpoints de Auth implementados

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/register` | Cria empresa + owner + subscription trial |
| POST | `/api/v1/auth/login` | Login com e-mail e senha |
| POST | `/api/v1/auth/refresh` | Renova tokens (rotation) |
| GET | `/api/v1/auth/me` | Dados do usuário autenticado |

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
| 1A | Estrutura base + Docker + Config | ✅ Concluída |
| 1B | Models SQLAlchemy 2.0 + Alembic | ✅ Concluída |
| 1C | Schemas Pydantic v2 | ✅ Concluída |
| 1D | Auth JWT (login, refresh, dependency) | ✅ Concluída |
| 1E | CRUD Base + Service Layer | ✅ Concluída |
| 1F | Endpoints REST /api/v1 | ✅ Concluída |
| 1G | Testes Automatizados pytest + httpx | ✅ Concluída — 68/68 |
| 2A | Frontend React + Vite + Tailwind | ⏳ Próxima |

---

## Decisões Pendentes

- [ ] `order_number` como `INTEGER` no banco (atual é VARCHAR)
- [ ] `assigned_to` no schema → renomear para `technician_id` para consistência
- [ ] Avaliar soft delete (`deleted_at`) vs `is_active`
- [ ] Avaliar `RefreshToken` model para blacklist
- [ ] Avaliar `Checklist/ChecklistItem` model (fase 2)
- [ ] Avaliar `computed_field` no config.py para DATABASE_URL automático