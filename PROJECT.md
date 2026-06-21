# ServiceFlow — Project Continuity Document

## Sessão Atual
**Fase:** 1C — Schemas Pydantic v2
**Status:** Aguardando

## Progresso das Fases

| Fase | Descrição | Status |
|------|-----------|--------|
| 1A | Estrutura base + Docker + Config | ✅ Concluída |
| 1B | Models SQLAlchemy 2.0 + Alembic | ✅ Concluída |
| 1C | Schemas Pydantic v2 | ⏳ Próxima |
| 1D | Auth JWT (login, refresh, dependency) | ⏳ Pendente |
| 1E | CRUD Base + Service Layer | ⏳ Pendente |
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

## Stack Técnica
- **Backend:** FastAPI + Python 3.14
- **ORM:** SQLAlchemy 2.0 (DeclarativeBase, Mapped, mapped_column)
- **Banco:** PostgreSQL 16 Alpine via Docker
- **Migrations:** Alembic 1.18.4
- **Validação:** Pydantic v2 + pydantic-settings
- **Auth:** python-jose + passlib (próxima fase)
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
└── backend/
    ├── app/
    │   ├── api/v1/endpoints/
    │   ├── core/
    │   │   └── config.py           ✅ pydantic-settings
    │   ├── db/
    │   │   ├── session.py
    │   │   └── base.py
    │   ├── models/                 ✅ COMPLETO
    │   │   ├── __init__.py         ← importa tudo (ponto central)
    │   │   ├── base.py             ← Base, UUIDMixin, TimestampMixin
    │   │   ├── company.py          ← tenant raiz + PlanTier enum
    │   │   ├── user.py             ← auth + UserRole RBAC
    │   │   ├── customer.py         ← cliente do tenant
    │   │   ├── service_order.py    ← OS + ServiceItem + enums
    │   │   └── subscription.py     ← controle de plano SaaS
    │   ├── schemas/                ⏳ fase 1C
    │   ├── services/               ⏳ fase 1E
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

### Enums definidos
- `PlanTier`: free / basico / pro / empresa
- `UserRole`: owner / admin / technician / viewer
- `OrderStatus`: draft → scheduled → in_progress → completed → invoiced / cancelled
- `OrderPriority`: low / normal / high / urgent
- `ItemType`: labor / part / travel / other
- `SubscriptionStatus`: trialing / active / past_due / cancelled / expired

## Comandos Úteis

```powershell
# Sempre rodar de dentro de backend/
cd backend

# Banco
docker compose up -d db
docker compose exec db psql -U serviceflow -d serviceflow_db -c "\dt"

# Migrations
python -m alembic revision --autogenerate -m "descricao"
python -m alembic upgrade head
python -m alembic downgrade -1

# App
docker compose up -d
docker compose logs -f api
```

## Variáveis de Ambiente (.env local)
```env
# ATENÇÃO: DATABASE_URL usa localhost para rodar alembic/app fora do Docker
# Dentro do Docker, o host é "db" (nome do serviço)
DATABASE_URL=postgresql+asyncpg://serviceflow:senha@localhost:5432/serviceflow_db
POSTGRES_HOST=localhost
```

## Decisões Pendentes / A Revisar
- [ ] Avaliar `computed_field` no config.py para gerar DATABASE_URL automaticamente
- [ ] Avaliar soft delete (`deleted_at`) vs `is_active` para auditoria
- [ ] Avaliar `RefreshToken` model separado para revogar tokens individuais
- [ ] Avaliar `Checklist/ChecklistItem` model (checklist de campo — fase 2)
- [ ] Definir estratégia de geração do `order_number` (ex: OS-2024-00042)