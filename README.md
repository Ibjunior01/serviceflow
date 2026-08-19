# ServiceFlow

> Field Service Management para técnicos de refrigeração e ar-condicionado no Brasil.

**🟢 Em produção:** https://serviceflow-liard.vercel.app

---

## Sumário

* [Sobre o Projeto](#sobre-o-projeto)
* [Stack Técnica](#stack-técnica)
* [Ambientes](#ambientes)
* [Estrutura de Pastas](#estrutura-de-pastas)
* [Pré-requisitos](#pré-requisitos)
* [Startup — Passo a Passo](#startup--passo-a-passo)
* [Comandos Úteis](#comandos-úteis)
* [Variáveis de Ambiente](#variáveis-de-ambiente)
* [Testes](#testes)
* [Deploy em Produção](#deploy-em-produção)
* [Arquitetura e Decisões Técnicas](#arquitetura-e-decisões-técnicas)
* [Autenticação, RBAC e Multi-tenancy](#autenticação-rbac-e-multi-tenancy)
* [Planos e Trial](#planos-e-trial)
* [Progresso das Fases](#progresso-das-fases)
* [Limitações Conhecidas e Roadmap Técnico](#limitações-conhecidas-e-roadmap-técnico)

---

## Sobre o Projeto

O **ServiceFlow** é um SaaS B2B de gestão de ordens de serviço voltado inicialmente para técnicos autônomos e pequenas empresas de refrigeração e ar-condicionado.

O sistema permite gerenciar:

* empresas;
* usuários e técnicos;
* clientes;
* ordens de serviço;
* atribuição de técnicos;
* prioridades;
* agendamentos;
* máquina de estados das OS;
* itens, peças e serviços por ordem;
* valores;
* planos e trial;
* limites de utilização por plano;
* dashboard operacional.

A aplicação utiliza arquitetura multi-tenant, mantendo os dados de cada empresa isolados por `company_id`.

O projeto possui frontend, backend e banco de dados e está publicado em ambiente de produção.

---

## Stack Técnica

| Camada                  | Tecnologia                                              |
| ----------------------- | ------------------------------------------------------- |
| Backend                 | FastAPI + Python 3.14                                   |
| ORM                     | SQLAlchemy 2 assíncrono                                 |
| Banco                   | PostgreSQL 16 local / PostgreSQL gerenciado em produção |
| Migrations              | Alembic                                                 |
| Validação               | Pydantic v2 + pydantic-settings                         |
| Autenticação            | JWT com `python-jose`                                   |
| Hash de senha           | passlib + bcrypt                                        |
| Driver PostgreSQL async | asyncpg                                                 |
| Testes                  | pytest + pytest-asyncio + httpx                         |
| Frontend                | React 19 + Vite + TypeScript                            |
| Estilização             | Tailwind CSS + shadcn/ui                                |
| Estado                  | Zustand                                                 |
| Data fetching           | TanStack Query                                          |
| Formulários             | React Hook Form + Zod                                   |
| HTTP Client             | Axios                                                   |
| Gráficos                | Recharts                                                |
| Deploy backend          | Render                                                  |
| Deploy frontend         | Vercel                                                  |

### Estado atual dos testes

```text
82 passed
```

A suíte backend está atualmente verde no ambiente local utilizado durante o processo de hardening.

---

## Ambientes

| Ambiente            | Frontend                       | Backend                                 | Banco de dados                        |
| ------------------- | ------------------------------ | --------------------------------------- | ------------------------------------- |
| **Desenvolvimento** | `localhost:5173`               | `localhost:8000`                        | PostgreSQL 16 local ou Docker Compose |
| **Produção**        | `serviceflow-liard.vercel.app` | `serviceflow-backend-5ljk.onrender.com` | PostgreSQL gerenciado pelo Render     |

> Os bancos de desenvolvimento, testes e produção devem permanecer completamente independentes.

Durante o hardening do projeto, a suíte backend também foi validada com:

```text
Windows
Python 3.14
PostgreSQL 16 local
venv
pytest
```

Portanto, Docker não é obrigatório para executar o ambiente de desenvolvimento.

---

## Estrutura de Pastas

```text
serviceflow/

├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py
│   │   │   ├── companies.py
│   │   │   ├── customers.py
│   │   │   ├── service_orders.py
│   │   │   └── users.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── exceptions.py
│   │   │   ├── rate_limit.py
│   │   │   └── security.py
│   │   │
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   │
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── alembic/
│   │   └── versions/
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_companies.py
│   │   ├── test_customers.py
│   │   ├── test_plans.py
│   │   ├── test_service_orders.py
│   │   └── test_users.py
│   │
│   ├── .env.example
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── requirements.lock
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── router/
│   │   ├── store/
│   │   └── types/
│   │
│   ├── package.json
│   ├── vite.config.ts
│   └── vercel.json
│
├── docker-compose.prod.yml
├── Caddyfile
├── PROJECT.md
└── README.md
```

> Ambientes virtuais como `.venv` e arquivos `.env` são locais e não devem ser versionados.

---

## Pré-requisitos

### Backend

* Python 3.14 recomendado;
* PostgreSQL 16;
* `venv`;
* Git.

### Frontend

* Node.js 20+;
* npm.

### Opcional

* Docker Desktop;
* Docker Compose;
* WSL2 no Windows.

O PostgreSQL pode ser executado diretamente no sistema operacional ou via Docker Compose.

---

# Startup — Passo a Passo

## Opção A — PostgreSQL instalado localmente

### 1. Backend

Entre na pasta:

```powershell
cd backend
```

Crie o ambiente virtual na primeira execução:

```powershell
python -m venv .venv
```

Ative:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
pip install -r requirements.lock
```

Configure o arquivo:

```text
backend/.env
```

Aplique as migrations:

```powershell
python -m alembic upgrade head
```

Execute a API:

```powershell
uvicorn app.main:app --reload
```

Swagger:

```text
http://localhost:8000/docs
```

---

### 2. Frontend

Em outro terminal:

```powershell
cd frontend
npm install
npm run dev
```

Aplicação:

```text
http://localhost:5173
```

---

## Opção B — PostgreSQL via Docker Compose

Dentro de:

```text
backend/
```

execute:

```powershell
docker compose up -d db
```

Depois:

```powershell
.\.venv\Scripts\Activate.ps1
python -m alembic upgrade head
uvicorn app.main:app --reload
```

---

## Comandos Úteis

### Ambiente Python

```powershell
cd backend

.\.venv\Scripts\Activate.ps1

python --version
pytest --version
```

### Banco via Docker

```powershell
docker compose up -d db

docker compose ps

docker compose logs -f db
```

### PostgreSQL local

```powershell
psql --version
```

Exemplo de conexão:

```powershell
psql -U serviceflow -h localhost -d serviceflow_db -W
```

### Migrations

```powershell
python -m alembic upgrade head
```

Criar nova migration:

```powershell
python -m alembic revision --autogenerate -m "descricao"
```

Rollback:

```powershell
python -m alembic downgrade -1
```

### API

```powershell
uvicorn app.main:app --reload
```

### Testes

```powershell
pytest -v
```

Ou:

```powershell
pytest -q
```

Parar no primeiro erro:

```powershell
pytest -x -v
```

Arquivo específico:

```powershell
pytest tests/test_auth.py -v
```

Ordens de serviço:

```powershell
pytest tests/test_service_orders.py -v
```

Planos:

```powershell
pytest tests/test_plans.py -v
```

### Frontend

```powershell
cd frontend

npm run dev
npm run build

npx tsc --noEmit
```

---

# Variáveis de Ambiente

## Backend — desenvolvimento

Exemplo:

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

SECRET_KEY=sua_chave_secreta_de_desenvolvimento

JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

Uma chave de desenvolvimento pode ser gerada com:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

> Nunca versionar arquivos `.env` nem utilizar a chave de desenvolvimento em produção.

---

## Ambiente de testes

O projeto utiliza PostgreSQL também durante os testes.

Exemplo:

```env
POSTGRES_USER=serviceflow
POSTGRES_PASSWORD=serviceflow123
POSTGRES_DB=serviceflow_test
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DATABASE_URL=postgresql+asyncpg://serviceflow:serviceflow123@localhost:5432/serviceflow_test

APP_NAME=ServiceFlow
APP_ENV=test
APP_VERSION=0.1.0

SECRET_KEY=chave_exclusiva_de_testes

JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=http://localhost:5173
```

> O banco de testes deve ser exclusivo. A suíte recria estruturas durante a execução e nunca deve apontar para banco de desenvolvimento ou produção contendo dados relevantes.

---

## Backend — produção

As variáveis de produção são configuradas diretamente no ambiente do Render.

Exemplo:

```text
APP_NAME=ServiceFlow
APP_ENV=production
APP_VERSION=0.1.0

SECRET_KEY=<segredo exclusivo de produção>

POSTGRES_USER=<gerado pelo provedor>
POSTGRES_PASSWORD=<gerado pelo provedor>
POSTGRES_DB=<gerado pelo provedor>
POSTGRES_HOST=<host>
POSTGRES_PORT=5432

DATABASE_URL=postgresql+asyncpg://<user>:<senha>@<host>/<db>

CORS_ORIGINS=https://serviceflow-liard.vercel.app
```

---

## Frontend — desenvolvimento

Quando `VITE_API_URL` não está definida, o cliente utiliza o proxy configurado pelo Vite para o backend local.

---

## Frontend — produção

```env
VITE_API_URL=https://serviceflow-backend-5ljk.onrender.com
```

---

# Testes

A suíte backend possui atualmente:

```text
82 testes automatizados passando
```

O conjunto cobre, entre outros pontos:

### Autenticação

* registro;
* login;
* senha incorreta;
* access token;
* refresh token;
* token inválido;
* usuário inativo;
* acesso a `/auth/me`.

### Autorização

* OWNER;
* ADMIN;
* TECHNICIAN;
* restrição de operações administrativas;
* escopo de ordens de serviço por técnico.

O papel `VIEWER` existe no domínio, mas sua política funcional específica ainda não está definida completamente.

### Multi-tenancy

Há testes garantindo isolamento entre empresas em recursos como:

* clientes;
* usuários;
* ordens de serviço.

### Ordens de serviço

Os testes cobrem:

* criação;
* atualização;
* listagem;
* paginação;
* detalhe;
* exclusão de rascunho;
* máquina de estados;
* transições válidas;
* transições inválidas;
* cancelamento;
* atribuição de técnico;
* itens;
* isolamento multi-tenant;
* escopo de acesso do TECHNICIAN;
* numeração por empresa.

### Planos

Há testes para:

* início de novo tenant em trial PRO;
* trial de aproximadamente 14 dias;
* expiração;
* downgrade para FREE;
* limite de técnicos no FREE;
* limite de clientes no FREE;
* limite mensal de ordens de serviço no FREE.

### Observação sobre rate limiting nos testes

O rate limiter da aplicação permanece ativo em runtime.

Na suíte geral ele é desabilitado para impedir que testes não relacionados a rate limiting interfiram entre si através do contador global de requisições.

---

# Deploy em Produção

## Backend + Banco — Render

O backend utiliza:

```text
backend/Dockerfile.prod
```

O banco PostgreSQL é gerenciado pelo Render.

O fluxo configurado inclui migrations Alembic antes da aplicação ser disponibilizada.

Health check:

```text
/health
```

O deploy é associado à branch `main`.

### Limitações atuais da infraestrutura gratuita

O ambiente gratuito pode apresentar:

* cold start após períodos de inatividade;
* limitações de recursos;
* restrições operacionais do serviço gerenciado.

Essas limitações são de infraestrutura e não da arquitetura lógica da aplicação.

---

## Frontend — Vercel

Root Directory:

```text
frontend
```

Framework:

```text
Vite
```

Variável de ambiente:

```text
VITE_API_URL
```

aponta para a API hospedada no Render.

---

# Arquitetura e Decisões Técnicas

O ServiceFlow segue atualmente uma arquitetura de **monólito modular**, adequada ao porte e ao estágio do produto.

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

Não há necessidade atual de microservices.

| Decisão                                 | Motivo                                              |
| --------------------------------------- | --------------------------------------------------- |
| FastAPI                                 | API tipada, assíncrona e com OpenAPI automático     |
| SQLAlchemy async                        | Integração assíncrona com PostgreSQL                |
| PostgreSQL                              | Integridade relacional e constraints transacionais  |
| UUID v4 como PK                         | Identificadores independentes da sequência do banco |
| Alembic                                 | Evolução versionada do schema                       |
| API `/api/v1`                           | Preparação para evolução futura do contrato         |
| Services                                | Centralização de regras de negócio                  |
| Repositories                            | Isolamento das consultas e persistência             |
| Pydantic                                | Validação do contrato de entrada e saída            |
| React + TypeScript                      | Frontend tipado e componentizado                    |
| TanStack Query                          | Cache e sincronização do estado remoto              |
| React Hook Form + Zod                   | Formulários e validação                             |
| Zustand                                 | Estado local compartilhado                          |
| `order_number` inteiro                  | Formatação visual pertence ao frontend              |
| Constraint `(company_id, order_number)` | Numeração independente entre tenants                |
| FSM de status                           | Impede transições inválidas da OS                   |

---

## Numeração das ordens

A unicidade do número da OS é definida por:

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

é válido.

Por outro lado:

```text
Empresa A → OS 1
Empresa A → OS 1
```

é rejeitado pelo banco.

A estratégia atual para obter o próximo número utiliza o maior número da empresa acrescido de um.

Essa solução é suficiente para o estágio atual do MVP, mas possui risco de colisão em requisições simultâneas e deverá ser endurecida antes de cenários de maior concorrência.

---

# Tabelas principais

| Tabela           | Model        | Descrição                    |
| ---------------- | ------------ | ---------------------------- |
| `companies`      | Company      | Tenant raiz                  |
| `users`          | User         | Usuários e RBAC              |
| `customers`      | Customer     | Clientes do tenant           |
| `service_orders` | ServiceOrder | Ordens de serviço            |
| `service_items`  | ServiceItem  | Itens, peças e serviços      |
| `subscriptions`  | Subscription | Plano e status da assinatura |

---

# Enums

| Enum               | Valores                                                            |
| ------------------ | ------------------------------------------------------------------ |
| PlanTier           | FREE / BASICO / PRO / EMPRESA                                      |
| UserRole           | OWNER / ADMIN / TECHNICIAN / VIEWER                                |
| OrderStatus        | DRAFT / SCHEDULED / IN_PROGRESS / COMPLETED / INVOICED / CANCELLED |
| OrderPriority      | LOW / NORMAL / HIGH / URGENT                                       |
| ItemType           | LABOR / PART / TRAVEL / OTHER                                      |
| SubscriptionStatus | TRIALING / ACTIVE / PAST_DUE / CANCELLED / EXPIRED                 |

---

# Máquina de Estados da OS

Transições permitidas:

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

INVOICED
 └─→ terminal

CANCELLED
 └─→ terminal
```

Transições fora desse fluxo são rejeitadas pela camada de serviço.

---

# Endpoints principais

| Método   | Rota                                  | Descrição                                      |
| -------- | ------------------------------------- | ---------------------------------------------- |
| POST     | `/api/v1/auth/register`               | Cria tenant, owner e subscription              |
| POST     | `/api/v1/auth/login`                  | Autenticação                                   |
| POST     | `/api/v1/auth/refresh`                | Emite novo par de tokens usando refresh válido |
| GET      | `/api/v1/auth/me`                     | Usuário autenticado                            |
| GET/POST | `/api/v1/customers`                   | Clientes                                       |
| GET/POST | `/api/v1/orders`                      | Ordens de serviço                              |
| GET      | `/api/v1/orders/{id}`                 | Detalhes da OS                                 |
| PATCH    | `/api/v1/orders/{id}`                 | Atualização da OS                              |
| PATCH    | `/api/v1/orders/{id}/status`          | Transição da máquina de estados                |
| GET/POST | `/api/v1/orders/{id}/items`           | Itens da OS                                    |
| DELETE   | `/api/v1/orders/{id}/items/{item_id}` | Remove item                                    |
| GET      | `/health`                             | Health check                                   |

---

# Autenticação, RBAC e Multi-tenancy

## JWT

O sistema utiliza:

```text
access token
refresh token
```

O frontend adiciona o access token às requisições através de interceptor Axios.

Em caso de `401`, o cliente pode utilizar o refresh token para solicitar novo par de tokens e repetir a requisição.

Atualmente, os tokens são persistidos no frontend.

O backend ainda não possui blacklist ou armazenamento server-side de refresh tokens.

Consequentemente, a emissão de um novo refresh token não invalida automaticamente o anterior.

Essa é uma limitação conhecida e faz parte do hardening de segurança planejado.

---

## RBAC

Atalhos existentes no backend:

```python
AdminOnly   # OWNER + ADMIN

OwnerOnly   # OWNER

TechOrAbove # OWNER + ADMIN + TECHNICIAN
```

### Ordens de serviço

Regra atualmente implementada e testada:

```text
OWNER
└─ todas as OS da empresa

ADMIN
└─ todas as OS da empresa

TECHNICIAN
└─ somente OS atribuídas a ele
```

O escopo do TECHNICIAN é aplicado em:

* listagem;
* detalhe;
* atualização;
* mudança de status;
* listagem de itens;
* adição de itens;
* remoção de itens.

O técnico também não pode reatribuir sua própria ordem de serviço para outro técnico.

### VIEWER

O papel `VIEWER` está modelado no domínio, porém sua política funcional específica ainda não foi definida completamente.

Ele não deve ser considerado um perfil de RBAC concluído até essa decisão ser formalizada e testada.

---

## Multi-tenancy

O `company_id` é utilizado como chave de isolamento de tenant.

Recursos de uma empresa não devem ser acessíveis por usuários de outra empresa.

Esse isolamento é aplicado nas consultas e possui testes específicos.

Para recursos pertencentes a outro tenant, a API evita expor o recurso ao usuário autenticado de outra empresa.

---

# Planos e Trial

| Plano   | Preço definido |
| ------- | -------------: |
| Free    |       R$ 0/mês |
| Básico  |      R$ 67/mês |
| Pro     |     R$ 127/mês |
| Empresa |     R$ 247/mês |

## Trial

Novos tenants iniciam atualmente em:

```text
Plano: PRO
Status: TRIALING
Duração aproximada: 14 dias
```

Após a expiração:

```text
PRO / TRIALING
        ↓
FREE / ACTIVE
```

A regra de expiração é atualmente aplicada de forma **lazy/on-request**.

Isso significa que a mudança de plano ocorre quando uma nova requisição autenticada processa a empresa após a data de término do trial.

Não existe atualmente um job em background dedicado exclusivamente a executar o downgrade no instante exato da expiração.

---

## Limites do plano FREE

Regras atualmente testadas:

| Recurso           |     Limite |
| ----------------- | ---------: |
| Técnicos          |          1 |
| Clientes          |          5 |
| Ordens de serviço | 10 por mês |

Quando o limite é atingido, a tentativa excedente é bloqueada.

---

# Segurança

Já existem no backend mecanismos como:

* autenticação JWT;
* hash de senha;
* RBAC;
* isolamento multi-tenant;
* rate limiting em rotas sensíveis de autenticação;
* security headers;
* CORS configurável por ambiente;
* tratamento centralizado de exceções;
* validação Pydantic.

Pontos ainda em hardening:

* estratégia de revogação de refresh token;
* armazenamento de tokens no frontend;
* logout server-side;
* revisão de CSP;
* hardening contra XSS;
* revisão final de secrets e logs.

---

# Progresso das Fases

| Fase | Descrição                                                              | Status                  |
| ---- | ---------------------------------------------------------------------- | ----------------------- |
| 1    | Backend, models, schemas, autenticação, CRUD, migrations e testes      | ✅ Concluída             |
| 2    | Frontend React + Vite + TypeScript                                     | ✅ Concluída             |
| 3    | Deploy Render + Vercel                                                 | ✅ Concluída             |
| 4    | Hardening inicial de model, multi-tenancy, HTTP contracts e RBAC de OS | ✅ Concluída             |
| 5    | Estabilização e ampliação da suíte backend                             | ✅ Concluída — 82 testes |
| 6    | Sincronização de documentação                                          | 🔄 Em andamento         |

---

# Limitações Conhecidas e Roadmap Técnico

## Segurança

* [ ] Avaliar estratégia server-side para refresh tokens
* [ ] Avaliar blacklist ou token families
* [ ] Revisar armazenamento de JWT no frontend
* [ ] Revisar CSP e proteção contra XSS
* [ ] Avaliar logout com revogação server-side

## Banco e concorrência

* [ ] Endurecer geração concorrente de `order_number`
* [ ] Revisar índices multi-tenant
* [ ] Validar migrations contra o schema final antes do fechamento do case

## Dashboard

* [ ] Criar endpoints agregados no backend para KPIs
* [ ] Remover dependência de agregações sobre apenas 50 OS no frontend

Atualmente o dashboard calcula parte dos indicadores sobre uma listagem limitada de ordens, o que pode gerar números incompletos quando a base ultrapassar esse limite.

## Frontend

* [ ] Revisar componentes e código residual do scaffold Vite
* [ ] Remover arquivos e imports comprovadamente abandonados
* [ ] Corrigir `toast.success` em fluxos de erro da `UsersPage`
* [ ] Revisar estados de loading, erro e empty state
* [ ] Revisar acessibilidade
* [ ] Avaliar code splitting por rota
* [ ] Reduzir estilos inline onde fizer sentido
* [ ] Revisar console logs residuais

## RBAC

* [ ] Definir política funcional do `VIEWER`
* [ ] Criar testes do `VIEWER` após formalizar a regra

## Contrato da API de OS

* [ ] Revisar campos expostos pelos schemas que ainda não possuem persistência correspondente
* [ ] Revisar criação de OS com `items`
* [ ] Revisar persistência de `technician_notes`

## Infraestrutura

* [ ] Alinhar versão Python do `backend/Dockerfile` de desenvolvimento com o ambiente oficial do projeto
* [ ] Criar pipeline de CI
* [ ] Executar testes backend em CI
* [ ] Executar TypeScript e build frontend em CI
* [ ] Revisar estratégia de hospedagem conforme crescimento do projeto

## Limpeza técnica

* [ ] Revisar warnings de Pydantic
* [ ] Revisar warnings de `pytest-asyncio`
* [ ] Revisar compatibilidade de dependências com Python 3.14
* [ ] Limpar duplicações no `requirements.txt`
* [ ] Revisar código residual antes do case final de portfólio

---

# Estado Atual

O ServiceFlow possui atualmente:

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
Dashboard                       IMPLEMENTADO COM LIMITAÇÃO
Deploy                          IMPLEMENTADO
Testes backend                  82 PASSANDO
CI                              NÃO IMPLEMENTADO
Revogação server-side JWT       NÃO IMPLEMENTADA
```

O projeto segue em processo de hardening antes da revisão final para apresentação como case principal de portfólio.
