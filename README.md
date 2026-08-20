# ServiceFlow

> SaaS B2B de Field Service Management para técnicos autônomos e pequenas empresas de refrigeração e ar-condicionado.

🟢 **Aplicação em produção:** https://serviceflow-liard.vercel.app  
📘 **API / Swagger:** https://serviceflow-backend-5ljk.onrender.com/docs

---

## Sobre o projeto

O ServiceFlow é uma aplicação web para gestão de operações de campo e ordens de serviço.

O projeto foi desenvolvido como um case Full Stack com foco em:

- arquitetura SaaS multi-tenant;
- autenticação e autorização;
- gestão de clientes;
- gestão de usuários e técnicos;
- ordens de serviço;
- itens, peças e serviços;
- máquina de estados das ordens;
- planos, trial e limites de utilização;
- dashboard operacional;
- testes automatizados;
- migrations versionadas;
- deploy separado de frontend, backend e banco de dados.

A arquitetura atual é um **monólito modular**, adequada ao porte e ao estágio do produto.

---

## Stack técnica

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI + Python 3.14 |
| ORM | SQLAlchemy 2 assíncrono |
| Banco | PostgreSQL |
| Driver PostgreSQL | asyncpg |
| Migrations | Alembic |
| Validação | Pydantic v2 + pydantic-settings |
| Autenticação | JWT com access token e refresh token |
| Hash de senha | passlib + bcrypt |
| Testes | pytest + pytest-asyncio + httpx |
| Frontend | React 19 + TypeScript + Vite |
| UI | Tailwind CSS + shadcn/ui |
| Estado | Zustand |
| Data fetching | TanStack Query |
| Formulários | React Hook Form + Zod |
| HTTP client | Axios |
| Gráficos | Recharts |
| Frontend em produção | Vercel |
| Backend em produção | Render |
| PostgreSQL em produção | Neon |
| Controle de versão | Git + GitHub |

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

Não há necessidade atual de microservices.

### Decisões principais

| Decisão | Motivo |
|---|---|
| FastAPI | API tipada, assíncrona e com OpenAPI automático |
| SQLAlchemy async | Integração assíncrona com PostgreSQL |
| PostgreSQL | Integridade relacional e constraints transacionais |
| UUID v4 como PK | Identificadores independentes da sequência do banco |
| Alembic | Evolução versionada do schema |
| API `/api/v1` | Versionamento do contrato HTTP |
| Services | Centralização das regras de negócio |
| Repositories | Isolamento da persistência |
| React + TypeScript | Frontend tipado e componentizado |
| TanStack Query | Cache e sincronização de estado remoto |
| Zustand | Estado local compartilhado |
| Constraint `(company_id, order_number)` | Numeração de OS independente por tenant |
| FSM de status | Bloqueio de transições inválidas |

---

## Estrutura principal

```text
serviceflow/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── alembic/
│   │   └── versions/
│   ├── tests/
│   ├── .env.example
│   ├── Dockerfile
│   ├── Dockerfile.prod
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── requirements.lock
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── router/
│   │   ├── store/
│   │   └── types/
│   ├── package.json
│   ├── vite.config.ts
│   └── vercel.json
├── docker-compose.prod.yml
├── Caddyfile
├── PROJECT.md
└── README.md
```

Arquivos `.env`, ambientes virtuais e credenciais de produção não devem ser versionados.

---

## Funcionalidades implementadas

O sistema possui atualmente:

- registro público de novas empresas;
- autenticação com JWT;
- access token e refresh token;
- recuperação do usuário autenticado;
- empresas como tenant raiz;
- usuários;
- técnicos;
- clientes;
- ordens de serviço;
- atribuição de técnico;
- prioridades;
- agendamento;
- itens de serviço;
- valores;
- máquina de estados da OS;
- planos;
- trial;
- limites do plano FREE;
- dashboard operacional;
- API REST versionada;
- OpenAPI / Swagger;
- migrations Alembic;
- testes automatizados;
- deploy em produção.

### Status funcional

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
CI                              NÃO IMPLEMENTADO
Revogação server-side JWT       NÃO IMPLEMENTADA
```

---

## Tabelas principais

| Tabela | Responsabilidade |
|---|---|
| `companies` | Tenant raiz |
| `users` | Usuários, técnicos e RBAC |
| `customers` | Clientes |
| `service_orders` | Ordens de serviço |
| `service_items` | Itens, peças e serviços |
| `subscriptions` | Plano e status da assinatura |
| `alembic_version` | Revisão do schema |

---

## Multi-tenancy

O `company_id` é utilizado como chave de isolamento entre tenants.

Recursos pertencentes a uma empresa não devem ser acessíveis por usuários de outra empresa.

Há cobertura automatizada para isolamento entre empresas em recursos como:

- clientes;
- usuários;
- ordens de serviço.

### Numeração das ordens

A unicidade da OS é definida por:

```text
(company_id, order_number)
```

Portanto é válido:

```text
Empresa A → OS 1
Empresa A → OS 2

Empresa B → OS 1
Empresa B → OS 2
```

A estratégia atual para determinar o próximo número utiliza o maior número da empresa acrescido de um.

Essa solução é adequada ao estágio atual do MVP, porém possui risco de colisão sob concorrência simultânea. A constraint do banco protege a integridade, mas a estratégia de geração deverá ser endurecida antes de cenários de maior concorrência.

---

## RBAC

Perfis modelados:

```text
OWNER
ADMIN
TECHNICIAN
VIEWER
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

O escopo do `TECHNICIAN` é aplicado em:

- listagem;
- detalhe;
- atualização;
- mudança de status;
- listagem de itens;
- inclusão de itens;
- remoção de itens.

O técnico também não pode reatribuir sua própria OS para outro técnico.

### VIEWER

O perfil `VIEWER` existe no domínio, mas sua política funcional específica ainda não foi formalizada completamente.

Por isso ele permanece classificado como **PARCIALMENTE IMPLEMENTADO**.

---

## Máquina de estados da OS

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

## Planos e trial

| Plano | Preço definido |
|---|---:|
| Free | R$ 0/mês |
| Básico | R$ 67/mês |
| Pro | R$ 127/mês |
| Empresa | R$ 247/mês |

### Trial

Novas empresas iniciam atualmente em:

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

O downgrade é aplicado de forma **lazy/on-request**: a mudança ocorre quando uma requisição autenticada processa a empresa após a data de expiração.

Não existe atualmente job em background dedicado a efetuar o downgrade no instante exato do vencimento.

### Limites do plano FREE

| Recurso | Limite |
|---|---:|
| Técnicos | 1 |
| Clientes | 5 |
| Ordens de serviço | 10 por mês |

Tentativas de ultrapassar os limites são bloqueadas pelo backend.

---

## Autenticação

O sistema utiliza:

```text
access token  → 30 minutos
refresh token → 7 dias
```

O frontend envia o access token através de interceptor Axios.

Quando uma requisição recebe `401`, o cliente pode utilizar o refresh token para solicitar um novo par de tokens e repetir a requisição original.

O fluxo de refresh possui tratamento de concorrência: requisições que aguardam uma renovação são liberadas quando o refresh funciona e rejeitadas corretamente quando a renovação falha.

### Limitação conhecida

Os tokens ainda são persistidos no `localStorage`.

O logout atual remove os tokens no cliente, porém o backend não mantém:

- blacklist;
- `jti` persistido;
- token family;
- sessão server-side;
- revogação imediata de refresh token.

A emissão de um novo refresh token não invalida automaticamente o anterior.

Para o escopo atual de MVP/portfólio, `localStorage`, logout client-side e ausência de revogação server-side foram mantidos como limitações documentadas.

Antes de cenários comerciais mais sensíveis, recomenda-se avaliar em conjunto refresh token server-side, revogação de sessão, `jti`/token family, detecção de reuse, cookie `HttpOnly`, estratégia CSRF e logout server-side real. Não foi criada uma rota de logout sem capacidade real de revogação.

---

## Segurança e hardening

Controles atualmente presentes:

- hashing de senha;
- JWT;
- separação entre access e refresh token;
- validação de usuário ativo;
- bloqueio de login/refresh para empresa inativa;
- RBAC;
- isolamento multi-tenant;
- rate limiting em rotas sensíveis;
- CORS configurado por ambiente;
- tratamento centralizado de exceções;
- validação Pydantic;
- headers HTTP de segurança;
- CSP bloqueante;
- Zod configurado em modo `jitless`;
- auditoria de dependências frontend;
- fila de refresh concorrente tratada;
- revisão de credenciais versionadas.

### Headers validados em produção

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Strict-Transport-Security
Content-Security-Policy
```

### Content Security Policy

A CSP está ativa em modo bloqueante em produção e não permite `unsafe-eval`.

Durante o hardening foi identificada uma tentativa de uso de `Function(...)` pelo mecanismo JIT do Zod 4.4.3. O frontend foi configurado com:

```ts
import { z } from 'zod'

z.config({
  jitless: true,
})

export { z }
```

Após a alteração, login, dashboard, clientes, ordens, criação de OS, detalhe da OS, inclusão de item e alteração de status foram validados em produção com o Console do navegador sem violações CSP.

O `'unsafe-inline'` permanece temporariamente apenas em `style-src`.

---

## Testes e validações

### Backend

Última suíte completa validada:

```text
86 passed
```

Ambiente utilizado durante o hardening:

```text
Windows
Python 3.14.6
PostgreSQL 16 local para testes
pytest 8.3.5
```

A suíte cobre, entre outros pontos:

- autenticação;
- access e refresh token;
- usuário inativo;
- empresa inativa;
- RBAC;
- multi-tenancy;
- ordens de serviço;
- máquina de estados;
- escopo de TECHNICIAN;
- numeração por empresa;
- trial;
- downgrade;
- limites FREE.

O rate limiter permanece ativo em runtime. Na suíte geral ele é desabilitado para evitar interferência entre testes não relacionados ao mecanismo de rate limiting.

### Frontend

Últimas validações:

```text
npm audit              → 0 vulnerabilities
npm audit --omit=dev   → 0 vulnerabilities
npx tsc --noEmit       → sem erros
npm run build          → concluído
```

O bundle principal ainda supera 500 kB após minificação. Isso é uma limitação de performance registrada para otimização posterior e não impede o funcionamento atual.

---

## Ambientes

| Ambiente | Frontend | Backend | Banco |
|---|---|---|---|
| Desenvolvimento | `localhost:5173` | `localhost:8000` | PostgreSQL local ou Docker |
| Testes | — | pytest | PostgreSQL de teste local |
| Produção | Vercel | Render | Neon PostgreSQL |

Os bancos de desenvolvimento, testes e produção devem permanecer independentes.

---

# Como executar localmente

## Pré-requisitos

### Backend

- Python 3.14;
- PostgreSQL;
- Git.

### Frontend

- Node.js 20+;
- npm.

### Opcional

- Docker Desktop;
- Docker Compose;
- WSL2 no Windows.

---

## Backend com PostgreSQL local

Entre no backend:

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

Configure:

```text
backend/.env
```

Aplique as migrations:

```powershell
python -m alembic upgrade head
```

Inicie a API:

```powershell
uvicorn app.main:app --reload
```

Swagger:

```text
http://localhost:8000/docs
```

---

## Frontend

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

## PostgreSQL via Docker Compose

Dentro de `backend/`:

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

## Variáveis de ambiente

### Backend — desenvolvimento

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

Nunca utilize credenciais de produção no repositório.

### Testes

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

O banco de testes deve ser exclusivo.

### Produção

As variáveis de produção do backend são configuradas diretamente no Render.

O PostgreSQL é hospedado no Neon.

Exemplo sem credenciais reais:

```env
APP_NAME=ServiceFlow
APP_ENV=production

SECRET_KEY=<segredo exclusivo de produção>

POSTGRES_USER=<usuario-do-provedor>
POSTGRES_PASSWORD=<senha-do-provedor>
POSTGRES_DB=<database>
POSTGRES_HOST=<host-do-neon>
POSTGRES_PORT=5432

DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>/<database>?ssl=require

CORS_ORIGINS=https://serviceflow-liard.vercel.app
```

Frontend:

```env
VITE_API_URL=https://serviceflow-backend-5ljk.onrender.com
```

Nenhum host privado, senha ou connection string real deve ser versionado.

---

# Deploy em produção

## Arquitetura de infraestrutura

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

- Provedor: Vercel
- Root Directory: `frontend`
- Framework: Vite
- URL: https://serviceflow-liard.vercel.app

### Backend

- Provedor: Render
- Container de produção: `backend/Dockerfile.prod`
- Health check: `/health`
- URL: https://serviceflow-backend-5ljk.onrender.com
- Deploy associado à branch `main`

### Banco de dados

- Provedor: Neon
- SGBD: PostgreSQL
- Controle de schema: Alembic
- Revisão validada em produção: `3e89efe30105`

O backend utiliza conexão SSL com o PostgreSQL gerenciado.

---

## Migração Render PostgreSQL → Neon

Em 20/08/2026, o PostgreSQL gratuito utilizado originalmente no Render expirou e ficou suspenso.

Como o ambiente continha somente dados de teste, não foi necessário preservar registros.

Foi criado um novo PostgreSQL no Neon e todo o schema foi reconstruído pelas migrations versionadas:

```text
06d5ab8065eb  initial_schema
533015c239d4  expand_customer_address_fields
885f034e93c2  order_number varchar to integer
3e89efe30105  order_number unique per company
```

A revisão final foi confirmada diretamente no banco:

```text
3e89efe30105
```

Após a troca das variáveis do Render foram validados:

```text
GET /health                         → 200 OK
Preflight CORS Vercel → Render     → 200 OK
```

Também foram validados pela aplicação publicada:

- registro e login;
- criação de empresa;
- criação de usuário;
- criação de subscription;
- criação de cliente;
- criação de OS;
- atribuição de técnico;
- inclusão de itens;
- alteração do status até `COMPLETED`;
- leitura pelo dashboard.

Consulta direta no Neon após a validação:

```text
companies        1
users            1
subscriptions    1
customers        1
service_orders   1
service_items    2
```

A mudança de provedor não exigiu alteração da arquitetura lógica, pois o sistema permaneceu utilizando PostgreSQL.

---

# Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/auth/register` | Cria tenant, owner e subscription |
| POST | `/api/v1/auth/login` | Autenticação |
| POST | `/api/v1/auth/refresh` | Emite novo par de tokens usando refresh válido |
| GET | `/api/v1/auth/me` | Usuário autenticado |
| GET/POST | `/api/v1/customers` | Clientes |
| GET/POST | `/api/v1/orders` | Ordens de serviço |
| GET | `/api/v1/orders/{id}` | Detalhes da OS |
| PATCH | `/api/v1/orders/{id}` | Atualização da OS |
| PATCH | `/api/v1/orders/{id}/status` | Transição da FSM |
| GET/POST | `/api/v1/orders/{id}/items` | Itens |
| DELETE | `/api/v1/orders/{id}/items/{item_id}` | Remove item |
| GET | `/health` | Health check |

---

# Limitações conhecidas e roadmap

## Segurança

Concluído:

- [x] investigar origem do `unsafe-eval`;
- [x] configurar Zod em modo `jitless`;
- [x] validar CSP em produção;
- [x] ativar CSP bloqueante;
- [x] validar aplicação com CSP bloqueante;
- [x] revisar secrets/credenciais versionadas;
- [x] manter credenciais reais de produção fora do Git.

Roadmap:

- [ ] avaliar refresh token server-side;
- [ ] avaliar blacklist, `jti` ou token families;
- [ ] revisar armazenamento de JWT antes de cenários mais sensíveis;
- [ ] avaliar cookie `HttpOnly`;
- [ ] implementar logout com revogação real caso sessões server-side sejam adotadas;
- [ ] reduzir dependência de `style-src 'unsafe-inline'` quando apropriado.

## Dashboard

- [ ] Criar endpoint agregado de KPIs no backend
- [ ] Remover dependência de cálculos sobre apenas as primeiras 50 OS

Atualmente parte dos indicadores é calculada no frontend a partir de uma listagem limitada, podendo produzir números incompletos quando a empresa ultrapassar esse volume.

## Banco e concorrência

- [ ] Endurecer geração concorrente de `order_number`
- [ ] Revisar índices multi-tenant

## Frontend

- [ ] Avaliar code splitting por rota
- [ ] Reduzir bundle principal
- [ ] Revisar código residual do scaffold
- [ ] Corrigir feedback de erro onde houver `toast.success`
- [ ] Revisar loading, error e empty states
- [ ] Revisar acessibilidade
- [ ] Reduzir estilos inline quando apropriado

## RBAC

- [ ] Formalizar política do `VIEWER`
- [ ] Criar testes após definição da regra

## Contrato da API de OS

- [ ] Revisar campos de schema ainda sem persistência correspondente
- [ ] Revisar criação de OS com `items`
- [ ] Revisar persistência de `technician_notes`

## Qualidade e infraestrutura

- [ ] Reduzir warnings de Pydantic / pytest-asyncio
- [ ] Revisar compatibilidade das dependências com Python 3.14
- [ ] Limpar duplicações de dependências
- [ ] Criar pipeline de CI
- [ ] Executar pytest em CI
- [ ] Executar TypeScript e build frontend em CI
- [ ] Fazer revisão final para portfólio

---

## Validação mais recente

```text
Backend
86 passed

Frontend
npm audit              0 vulnerabilities
npm audit --omit=dev   0 vulnerabilities
npx tsc --noEmit       OK
npm run build          OK

Produção
Vercel                  OK
Render /health          200 OK
CORS                     OK
Neon PostgreSQL          OK
Alembic head             3e89efe30105
CSP bloqueante           OK
Console CSP              sem violações nos fluxos validados
```

---

## Estado do projeto

O ServiceFlow está funcional e publicado, com arquitetura multi-tenant, autenticação, RBAC, regras de negócio, migrations e testes automatizados.

A **ETAPA 7 — Segurança e hardening** está concluída para o escopo atual. O próximo trabalho técnico é a **ETAPA 8 — Dashboard e agregações**, seguida de limpeza técnica, CI e revisão final para portfólio.
