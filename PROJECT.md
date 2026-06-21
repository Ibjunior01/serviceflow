## Sessão Atual
**Fase:** 1B — Models SQLAlchemy 2.0
**Status:** Aguardando

## Decisões de Arquitetura Tomadas
- Async engine (asyncpg) para performance sob carga
- Versionamento de API em /api/v1 desde o início
- Settings via pydantic-settings com validação no boot
- Docker Compose como ambiente padrão (PostgreSQL + FastAPI)
- WSL 2 como engine do Docker no Windows

## Estrutura de Pastas (estado atual)
serviceflow/
└── backend/
    ├── app/
    │   ├── api/v1/endpoints/
    │   ├── core/config.py
    │   ├── db/session.py, base.py
    │   ├── models/
    │   ├── schemas/
    │   ├── services/
    │   └── main.py
    ├── .env
    ├── docker-compose.yml
    ├── Dockerfile
    └── requirements.txt