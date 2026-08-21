# SERVICEFLOW_PORTFOLIO_STATE

## 1. Identificação do projeto

**Projeto:** ServiceFlow  
**Categoria:** SaaS B2B / Field Service Management  
**Objetivo:** gestão de clientes, técnicos e ordens de serviço para operações de campo, com arquitetura multi-tenant, autenticação, regras de negócio, dashboard, testes automatizados, CI e deploy em produção.

Este documento registra apenas funcionalidades e características que foram comprovadas durante a revisão técnica do projeto.

---

# 2. Resumo executivo

O ServiceFlow está funcional e publicado, com frontend em React/TypeScript, backend em FastAPI e banco PostgreSQL.

Arquitetura validada:

```text
Vercel
React / TypeScript / Vite
        │
        ▼
Render
FastAPI
        │
        ▼
Neon
PostgreSQL
```

O projeto utiliza um **monólito modular**, com separação entre:

```text
API
↓
Services
↓
Repositories
↓
SQLAlchemy Async
↓
PostgreSQL
```

Estado geral:

```text
Aplicação publicada                    IMPLEMENTADO
Backend FastAPI                        IMPLEMENTADO
Frontend React                         IMPLEMENTADO
PostgreSQL                             IMPLEMENTADO
Alembic                                IMPLEMENTADO
Multi-tenancy                          IMPLEMENTADO
JWT                                    IMPLEMENTADO
RBAC OWNER/ADMIN/TECHNICIAN            IMPLEMENTADO
RBAC VIEWER                            PARCIAL
FSM de ordens                          IMPLEMENTADO
Planos / trial                         IMPLEMENTADO
Limites FREE                           IMPLEMENTADO
Dashboard agregado                     IMPLEMENTADO
Testes automatizados                   IMPLEMENTADO
CSP bloqueante                         IMPLEMENTADO
CI GitHub Actions                      IMPLEMENTADO
Code splitting                         IMPLEMENTADO
Revogação server-side de JWT           NÃO IMPLEMENTADO
```

---

# 3. Stack comprovada

## Backend

- Python 3.14
- FastAPI
- SQLAlchemy 2 assíncrono
- PostgreSQL
- asyncpg
- Alembic
- Pydantic v2
- JWT
- passlib
- bcrypt
- pytest 9.1.1
- pytest-asyncio 1.4.0
- httpx
- SlowAPI

## Frontend

- React 19
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Zustand
- TanStack Query
- Axios
- React Hook Form
- Zod
- Recharts
- React Router

## Infraestrutura

- Vercel — frontend
- Render — backend
- Neon — PostgreSQL
- GitHub — controle de versão
- GitHub Actions — CI

---

# 4. Arquitetura

## Classificação

**IMPLEMENTADO**

O projeto segue arquitetura de monólito modular.

```text
React / TypeScript
        ↓
Axios / TanStack Query
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

### Características comprovadas

- API versionada em `/api/v1`;
- separação entre endpoints, services e repositories;
- ORM assíncrono;
- migrations com Alembic;
- banco relacional PostgreSQL;
- frontend e backend implantados separadamente;
- banco de produção desacoplado da aplicação.

### Decisão arquitetural

Não há evidência de necessidade atual de microservices.

Para o escopo atual, o monólito modular é uma solução adequada porque reduz complexidade operacional sem eliminar separação de responsabilidades.

---

# 5. Multi-tenancy

## Classificação

**IMPLEMENTADO**

A empresa é o tenant raiz do sistema.

O isolamento utiliza `company_id`.

Há cobertura automatizada para isolamento entre tenants em recursos relevantes.

### Numeração das ordens

A unicidade de uma ordem é:

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

O mesmo `order_number` pode existir em empresas diferentes.

Não pode existir duplicidade do mesmo número dentro do mesmo tenant.

### Proteção de banco

Existe constraint composta:

```text
(company_id, order_number)
```

### Limitação conhecida

A geração atual utiliza:

```text
MAX(order_number) + 1
```

Esse algoritmo pode sofrer colisão em concorrência simultânea.

A constraint garante integridade do banco, porém uma das requisições concorrentes pode falhar.

**Classificação desta limitação:** ROADMAP.

---

# 6. Autenticação JWT

## Classificação

**IMPLEMENTADO COM LIMITAÇÕES DOCUMENTADAS**

Configuração validada:

```text
Access token   30 minutos
Refresh token   7 dias
```

### Implementado

- login;
- access token;
- refresh token;
- diferenciação de tipo de token;
- access token não pode funcionar como refresh;
- refresh token não pode funcionar como access;
- usuário inativo bloqueado;
- empresa inativa bloqueada no login;
- empresa inativa bloqueada no refresh;
- interceptor Axios;
- fila concorrente de refresh;
- limpeza de autenticação após falha de refresh.

### Fluxo da fila de refresh

```text
refresh OK
→ libera requisições pendentes

refresh falha
→ rejeita requisições pendentes
→ limpa autenticação local
→ redireciona para login
```

---

# 7. Sessão e revogação

## Classificação

**NÃO IMPLEMENTADO / ROADMAP**

Os tokens permanecem armazenados no `localStorage`.

O backend não mantém atualmente:

- blacklist;
- `jti` persistido;
- token family;
- tabela de sessões;
- token version;
- detecção de reuse;
- revogação server-side imediata;
- logout server-side real.

O logout atual é client-side.

### Decisão atual

A solução foi mantida para o escopo de MVP/portfólio com a limitação explicitamente documentada.

### Roadmap de segurança

Antes de uso comercial mais sensível, avaliar em conjunto:

- refresh server-side;
- revogação de sessão;
- token family;
- detecção de reuse;
- cookie `HttpOnly`;
- CSRF;
- logout server-side real.

---

# 8. RBAC

## OWNER / ADMIN / TECHNICIAN

**IMPLEMENTADO**

Regra comprovada para ordens:

```text
OWNER
└─ todas as OS do tenant

ADMIN
└─ todas as OS do tenant

TECHNICIAN
└─ apenas OS atribuídas ao próprio técnico
```

O escopo do técnico é aplicado em:

- listagem de ordens;
- detalhe;
- atualização;
- mudança de status;
- listagem de itens;
- inclusão de itens;
- remoção de itens.

O técnico também não pode reatribuir a própria OS para outro técnico.

## VIEWER

**PARCIAL**

O perfil existe no domínio.

A política funcional específica não foi formalizada integralmente.

Não deve ser apresentado como perfil finalizado até que a regra seja definida e testada.

---

# 9. Máquina de estados das ordens

## Classificação

**IMPLEMENTADO**

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

INVOICED  → terminal
CANCELLED → terminal
```

Transições inválidas são rejeitadas pela camada de serviço.

---

# 10. Clientes, usuários e técnicos

## Classificação

**IMPLEMENTADO**

O sistema possui recursos para:

- clientes;
- usuários;
- técnicos;
- associação de técnicos às ordens;
- isolamento por empresa.

Não há evidência de que funcionalidades além do escopo atual devam ser apresentadas como concluídas.

---

# 11. Ordens de serviço

## Classificação

**IMPLEMENTADO**

Funcionalidades comprovadas:

- criação de OS;
- número por tenant;
- prioridade;
- agendamento;
- atribuição de técnico;
- atualização;
- visualização;
- mudança de status;
- itens de serviço;
- valores;
- FSM;
- isolamento por tenant;
- escopo de técnico.

### Pendências de contrato

**PARCIAL / ROADMAP**

Precisam de revisão específica antes de serem promovidas como funcionalidades completas:

- alguns campos de schema sem persistência equivalente confirmada;
- `technician_notes`;
- criação de OS diretamente com `items`;
- campos adicionais de equipamento/endereço.

---

# 12. Planos e trial

## Classificação

**IMPLEMENTADO**

Planos modelados:

```text
FREE
BASICO
PRO
EMPRESA
```

Preços documentados:

```text
FREE      R$ 0/mês
BASICO    R$ 67/mês
PRO       R$ 127/mês
EMPRESA   R$ 247/mês
```

### Trial

Novas empresas iniciam em:

```text
PRO / TRIALING
aproximadamente 14 dias
```

Após expiração:

```text
PRO / TRIALING
       ↓
FREE / ACTIVE
```

O downgrade é aplicado de forma lazy/on-request.

Não existe job em background para realizar a mudança exatamente no instante da expiração.

### Limites FREE

**IMPLEMENTADO E TESTADO**

```text
Técnicos             1
Clientes             5
Ordens de serviço   10 por mês
```

Tentativas de ultrapassar os limites são bloqueadas pelo backend.

---

# 13. Dashboard

## Classificação

**IMPLEMENTADO**

A limitação original do dashboard foi corrigida.

### Problema anterior

O frontend buscava somente:

```text
page_size=50
```

e calculava indicadores sobre essa amostra.

Com mais de 50 ordens, os KPIs poderiam ficar incorretos.

### Solução atual

Endpoint:

```text
GET /api/v1/dashboard/summary
```

Agregações no backend:

- quantidade por status;
- ordens por mês;
- seis meses mais recentes;
- meses sem movimento preenchidos com zero;
- oito ordens recentes.

### RBAC do dashboard

```text
OWNER / ADMIN
→ todo o tenant

TECHNICIAN
→ apenas ordens atribuídas ao próprio técnico
```

### Testes específicos

Há cobertura para:

- mais de 50 ordens;
- dashboard vazio;
- isolamento entre tenants;
- escopo de técnico.

A limitação de 50 ordens foi removida.

---

# 14. Segurança frontend

## Classificação

**IMPLEMENTADO**

### Headers validados

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Strict-Transport-Security
Content-Security-Policy
```

### CSP

**IMPLEMENTADO**

A Content Security Policy está em modo bloqueante.

`unsafe-eval` não é permitido.

### Zod

Foi identificado uso de geração dinâmica de função pelo mecanismo JIT do Zod.

A aplicação passou a utilizar Zod em modo:

```text
jitless
```

Após a alteração, os principais fluxos foram validados sem violações CSP no console.

### Limitação conhecida

`style-src 'unsafe-inline'` ainda permanece temporariamente.

**Classificação:** ROADMAP.

---

# 15. Dependências frontend

## Classificação

**IMPLEMENTADO / VALIDADO**

Auditoria atual:

```text
npm audit
0 vulnerabilities

npm audit --omit=dev
0 vulnerabilities
```

---

# 16. Code splitting

## Classificação

**IMPLEMENTADO**

As páginas passaram a ser carregadas por rota com:

```text
React.lazy
Suspense
```

### Resultado medido

Antes:

```text
Bundle principal
~1.060,76 kB

gzip
~317,51 kB
```

Depois:

```text
Bundle principal
~351,61 kB

gzip
~109,32 kB
```

Redução aproximada do JavaScript inicial:

```text
~67%
```

O Dashboard, que utiliza Recharts, passou a ser carregado em chunk separado.

Build validado sem chunk acima de 500 kB.

---

# 17. Qualidade backend

## Classificação

**IMPLEMENTADO / VALIDADO**

Estado atual:

```text
pytest -q
90 passed, 2 warnings
```

### Warnings

O projeto chegou a apresentar milhares de warnings durante o hardening.

Após limpeza:

```text
5453 → 2
```

Os dois warnings restantes são originados no SlowAPI sob Python 3.14.

Eles não são mascarados.

### Dependências

```text
python -m pip check
No broken requirements found.
```

Versões de teste alinhadas:

```text
pytest==9.1.1
pytest-asyncio==1.4.0
```

---

# 18. Cobertura funcional dos testes

A suíte contém cobertura comprovada para:

- autenticação;
- access token;
- refresh token;
- usuário inativo;
- empresa inativa;
- multi-tenancy;
- RBAC;
- clientes;
- usuários;
- ordens;
- FSM;
- escopo de TECHNICIAN;
- numeração por empresa;
- trial;
- downgrade;
- limites FREE;
- dashboard.

O rate limiter permanece ativo em runtime e é desabilitado na suíte geral para impedir interferência de contadores entre testes não relacionados ao mecanismo de rate limiting.

---

# 19. CI — GitHub Actions

## Classificação

**IMPLEMENTADO**

Workflow:

```text
.github/workflows/ci.yml
```

Gatilhos:

- push para `main`;
- pull request para `main`;
- execução manual.

## Backend CI

Ambiente:

```text
Ubuntu
Python 3.14
PostgreSQL 16 descartável
```

Etapas:

```text
checkout
↓
install requirements.lock
↓
pip check
↓
Alembic upgrade head
↓
pytest -q
```

Resultado validado:

```text
Backend ✅
```

## Frontend CI

Ambiente:

```text
Ubuntu
Node 24
```

Etapas:

```text
checkout
↓
npm ci
↓
TypeScript
↓
Vite build
↓
npm audit
↓
npm audit --omit=dev
```

Resultado validado:

```text
Frontend ✅
```

O CI não utiliza Neon, Render nem credenciais de produção.

---

# 20. Banco e migrations

## Classificação

**IMPLEMENTADO**

Produção utiliza PostgreSQL no Neon.

Schema controlado por Alembic.

Migrations confirmadas:

```text
06d5ab8065eb  initial_schema
533015c239d4  expand_customer_address_fields
885f034e93c2  order_number varchar to integer
3e89efe30105  order_number unique per company
```

Head validado:

```text
3e89efe30105
```

---

# 21. Migração Render PostgreSQL → Neon

## Classificação

**CONCLUÍDA**

O PostgreSQL gratuito usado originalmente no Render expirou.

Como o banco continha somente dados de teste:

```text
não houve migração de dados históricos
```

Foi criado um PostgreSQL novo no Neon e o schema foi reconstruído com Alembic.

Validações realizadas:

- conexão;
- migrations;
- health check;
- CORS;
- registro/login;
- cliente;
- OS;
- técnico;
- itens;
- status;
- dashboard;
- consulta direta ao banco.

Arquitetura atual:

```text
Frontend     Vercel
Backend      Render
Database     Neon
```

---

# 22. Deploy

## Classificação

**IMPLEMENTADO**

Frontend:

```text
Vercel
```

Backend:

```text
Render
```

Banco:

```text
Neon PostgreSQL
```

Health endpoint:

```text
GET /health
```

validado com HTTP 200.

---

# 23. Secrets e credenciais

## Classificação

**VALIDADO**

Foi executada busca no Git por:

- `SECRET_KEY`;
- `POSTGRES_PASSWORD`;
- `DATABASE_URL`;
- host Neon;
- URLs e credenciais relevantes.

Resultado:

- nenhuma senha real do Neon encontrada versionada;
- nenhum host real `*.neon.tech` encontrado versionado;
- `.env.test` contém apenas credenciais locais/de teste;
- `SECRET_KEY` de teste é fictícia;
- secrets reais permanecem fora do Git.

---

# 24. Limpeza técnica

## Classificação

**CONCLUÍDA PARA O ESCOPO ATUAL**

Executado:

- remoção de arquivo frontend vazio;
- correção de feedbacks incorretos com `toast.success`;
- modernização da configuração Pydantic;
- atualização do pytest-asyncio;
- alinhamento da versão do pytest;
- redução de warnings;
- auditoria de encoding;
- busca por logs/debug residuais;
- code splitting;
- auditoria npm;
- build e TypeScript.

Buscas finais não localizaram resíduos relevantes de:

```text
console.log
console.debug
breakpoint
pdb
toast.success('Erro')
```

---

# 25. Funcionalidades parcialmente implementadas

## VIEWER

**PARCIAL**

O papel existe, mas sua política completa não foi definida.

## Contrato de alguns campos da OS

**PARCIAL**

Há schemas/campos que ainda exigem alinhamento com persistência antes de serem tratados como funcionalidades completas.

---

# 26. Funcionalidades não implementadas

Os itens abaixo não devem ser apresentados como funcionalidades atuais:

- revogação server-side de JWT;
- blacklist de tokens;
- token family persistida;
- `jti` persistido;
- logout server-side real;
- sessão server-side;
- job dedicado para expiração de trial;
- política completa do VIEWER.

---

# 27. Roadmap técnico

## Segurança

- revogação server-side;
- token family / `jti`;
- detecção de reuse;
- cookies `HttpOnly`;
- CSRF;
- logout real;
- redução de `style-src 'unsafe-inline'`.

## Banco

- estratégia concorrente mais robusta para `order_number`;
- revisão de índices multi-tenant quando houver carga real.

## API

- revisar `technician_notes`;
- revisar criação de OS com `items`;
- alinhar schemas e persistência restantes.

## RBAC

- formalizar VIEWER;
- criar testes depois da definição.

## Frontend

- auditoria específica de acessibilidade;
- novas otimizações de bundle apenas se métricas reais justificarem.

## Dependências

- acompanhar compatibilidade futura do SlowAPI com Python 3.14.

---

# 28. Evidências de validação

## Backend

```text
90 passed
2 warnings
pip check OK
```

## Frontend

```text
TypeScript         OK
Build              OK
npm audit          0 vulnerabilities
npm audit --omit=dev
                   0 vulnerabilities
```

## Performance de bundle

```text
Antes             ~1.060,76 kB
Depois            ~351,61 kB
Redução inicial   ~67%
```

## CI

```text
Backend   ✅
Frontend  ✅
```

## Produção

```text
Vercel             OK
Render             OK
Neon PostgreSQL    OK
Health             200
CORS               OK
CSP bloqueante     OK
```

---

# 29. Classificação final

## IMPLEMENTADO

- backend FastAPI;
- frontend React;
- PostgreSQL;
- migrations Alembic;
- multi-tenancy;
- isolamento por empresa;
- JWT access/refresh;
- bloqueio de usuário/empresa inativos;
- RBAC OWNER;
- RBAC ADMIN;
- RBAC TECHNICIAN;
- clientes;
- usuários;
- técnicos;
- ordens;
- itens;
- FSM;
- planos;
- trial;
- downgrade FREE;
- limites FREE;
- dashboard agregado;
- testes automatizados;
- CSP bloqueante;
- headers de segurança;
- Zod jitless;
- auditoria de dependências;
- code splitting;
- deploy;
- CI.

## PARCIAL

- VIEWER;
- alguns campos do contrato de OS ainda sem persistência confirmada.

## NÃO IMPLEMENTADO

- revogação server-side;
- sessão server-side;
- blacklist;
- token family persistida;
- logout server-side real;
- job de expiração de trial.

## ROADMAP

- hardening concorrente de `order_number`;
- arquitetura de sessão mais forte;
- política VIEWER;
- revisão final do contrato da OS;
- acessibilidade;
- redução de `unsafe-inline`;
- acompanhamento do SlowAPI.

---

# 30. Avaliação para portfólio

O ServiceFlow pode ser apresentado como um **case Full Stack profissional** porque demonstra, de forma comprovada:

- modelagem de SaaS multi-tenant;
- regras de autorização;
- autenticação JWT;
- regras de negócio com FSM;
- banco relacional;
- migrations;
- arquitetura em camadas;
- integração frontend/backend;
- dashboard com agregações server-side;
- testes automatizados;
- hardening de segurança;
- tratamento de dívida técnica;
- otimização de bundle;
- CI;
- deploy em serviços reais.

É importante manter explícita a distinção entre:

```text
o que existe
o que existe parcialmente
o que não existe
o que está planejado
```

Essa distinção aumenta a credibilidade técnica do case.

---

# 31. Estado final do case

```text
Arquitetura                 VALIDADA
Multi-tenancy               VALIDADO
RBAC principal              VALIDADO
JWT                         VALIDADO
FSM                         VALIDADA
Planos / trial              VALIDADOS
Dashboard                   VALIDADO
Backend                     90 TESTES
Frontend                    BUILD VERDE
Dependências frontend       0 VULNERABILIDADES
CI                          VERDE
Deploy                      FUNCIONAL
Documentação técnica        SINCRONIZADA NA ETAPA FINAL
```

**Status do ServiceFlow:** pronto para fechamento como case de portfólio, mantendo as limitações e itens de roadmap explicitamente documentados.
