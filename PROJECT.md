# ServiceFlow — Project Continuity Document

## Sessão atual

**Data de referência:** 20/08/2026  
**Fase:** Hardening técnico concluído; próxima fase: dashboard e agregações  
**Status:** aplicação publicada e funcional, com frontend na Vercel, backend no Render e PostgreSQL no Neon. Migração de banco concluída. ETAPA 7 de segurança concluída para o escopo atual. Backend com 86 testes aprovados e frontend com build, TypeScript, npm audit e CSP bloqueante validados.

### URLs de produção

- **Frontend:** https://serviceflow-liard.vercel.app
- **Backend:** https://serviceflow-backend-5ljk.onrender.com
- **Swagger:** https://serviceflow-backend-5ljk.onrender.com/docs
- **Health:** https://serviceflow-backend-5ljk.onrender.com/health

---

# 1. Objetivo do projeto

O ServiceFlow é um SaaS B2B de Field Service Management voltado inicialmente para técnicos autônomos e pequenas empresas de refrigeração e ar-condicionado.

O projeto é utilizado como case de portfólio Full Stack.

A prioridade atual não é adicionar funcionalidades indiscriminadamente.

O foco é:

- consistência entre código, testes, migrations e documentação;
- isolamento multi-tenant;
- autorização;
- segurança;
- qualidade da suíte;
- arquitetura;
- infraestrutura;
- preparação do case profissional.

---

# 2. Stack confirmada

## Backend

- Python 3.14;
- FastAPI;
- SQLAlchemy 2 assíncrono;
- PostgreSQL;
- asyncpg;
- Alembic;
- Pydantic v2;
- JWT;
- passlib + bcrypt;
- pytest;
- pytest-asyncio;
- httpx.

## Frontend

- React 19;
- TypeScript;
- Vite;
- Tailwind CSS;
- shadcn/ui;
- Zustand;
- TanStack Query;
- Axios;
- React Hook Form;
- Zod;
- Recharts.

## Infraestrutura atual

```text
Vercel
React / Vite
        │
        ▼
Render
FastAPI
        │
        ▼
Neon
PostgreSQL
```

## Desenvolvimento / validação local

Último ambiente validado:

```text
Windows
Python 3.14.6
pytest 8.3.5
PostgreSQL 16 local
Node 24.19.0
npm 11.17.0
```

O servidor Neon validado utiliza PostgreSQL 18.6.

---

# 3. Arquitetura

O projeto segue um monólito modular:

```text
Frontend React
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

Essa arquitetura continua adequada ao porte e ao estágio atual.

Não há justificativa para microservices neste momento.

---

# 4. Estado funcional comprovado

```text
Backend FastAPI                 IMPLEMENTADO
Frontend React                  IMPLEMENTADO
PostgreSQL                      IMPLEMENTADO
Alembic                         IMPLEMENTADO
JWT                             IMPLEMENTADO
RBAC OWNER/ADMIN/TECHNICIAN     IMPLEMENTADO
RBAC VIEWER                     PARCIALMENTE IMPLEMENTADO
Multi-tenancy                   IMPLEMENTADO
FSM de Ordens                   IMPLEMENTADO
Trial PRO                       IMPLEMENTADO
Downgrade FREE                  IMPLEMENTADO
Limites FREE                    IMPLEMENTADO
Dashboard                       IMPLEMENTADO COM LIMITAÇÃO
Deploy                          IMPLEMENTADO
Security headers                IMPLEMENTADO
CSP bloqueante                  NÃO IMPLEMENTADA
CI                              NÃO IMPLEMENTADO
Revogação server-side JWT       NÃO IMPLEMENTADA
```

---

# 5. Regras de negócio confirmadas

## 5.1 Numeração das ordens

A unicidade é:

```text
(company_id, order_number)
```

O model e a migration estão alinhados.

É permitido:

```text
Empresa A → OS 1
Empresa B → OS 1
```

Não é permitido duplicar o mesmo `order_number` dentro da mesma empresa.

A geração atual utiliza `MAX(order_number) + 1` por empresa.

Risco conhecido: concorrência simultânea pode gerar colisão. A constraint preserva integridade, porém uma requisição concorrente pode falhar. Hardening futuro recomendado.

## 5.2 Máquina de estados

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

## 5.3 RBAC de ordens

```text
OWNER
└─ todas as OS do tenant

ADMIN
└─ todas as OS do tenant

TECHNICIAN
└─ apenas OS atribuídas ao próprio técnico
```

O escopo do técnico foi aplicado em:

- listagem;
- detalhe;
- atualização;
- mudança de status;
- listagem de itens;
- adição de itens;
- remoção de itens.

O técnico não pode reatribuir sua própria OS para outro técnico.

## 5.4 VIEWER

O enum existe no domínio.

A política funcional específica ainda não foi definida integralmente.

Status:

```text
PARCIALMENTE IMPLEMENTADO
```

Não criar testes definitivos antes de formalizar a regra.

---

# 6. Planos e trial

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

Novas empresas iniciam em:

```text
PRO / TRIALING
aproximadamente 14 dias
```

Após a expiração:

```text
PRO / TRIALING
       ↓
FREE / ACTIVE
```

O downgrade é lazy/on-request.

Não há job em background para aplicar a mudança no instante exato da expiração.

### Limites FREE testados

```text
Técnicos             1
Clientes             5
Ordens de serviço   10 por mês
```

---

# 7. Hardening executado

## ETAPA 1 — Auditoria

Concluída.

Achados principais:

- drift entre model e migration de `order_number`;
- testes aceitando HTTP 500;
- regra TECHNICIAN inconsistente;
- divergências README / código;
- risco de concorrência em numeração;
- limitações JWT;
- dashboard limitado a 50 registros;
- itens residuais de frontend;
- política VIEWER incompleta.

---

## ETAPA 2 — `order_number` multi-tenant

Concluída.

Alterações:

- removida unicidade global;
- adicionada `UniqueConstraint("company_id", "order_number")`;
- model alinhado à migration existente;
- testes para duplicidade no mesmo tenant;
- testes permitindo mesmo número em tenants diferentes.

Migration correspondente:

```text
3e89efe30105
order_number unique per company
```

Commit:

```text
4e0dda4 fix: enforce service order tenant and technician scope
```

---

## ETAPA 3 — testes aceitando HTTP 500

Concluída.

Os asserts que aceitavam `(200, 500)` foram substituídos pelo contrato HTTP esperado.

HTTP 500 não é mais tratado como comportamento válido nesses testes.

---

## ETAPA 4 — acesso TECHNICIAN

Concluída.

Regra escolhida:

```text
OWNER / ADMIN → todas as OS do tenant
TECHNICIAN    → apenas OS atribuídas a ele
```

Cobertura adicionada para:

- listagem;
- detalhe;
- status;
- itens;
- tentativa de reatribuição.

Commit relacionado:

```text
4e0dda4 fix: enforce service order tenant and technician scope
```

---

## ETAPA 5 — estabilização da suíte

Concluída.

O rate limiter permanece ativo em runtime.

Na suíte geral ele é desabilitado para evitar interferência de contadores globais entre testes não relacionados ao rate limiting.

Foram adicionados testes de:

- usuário inativo;
- empresa inativa;
- trial;
- downgrade;
- limites FREE.

Commit:

```text
36f6d23 test: add plan limits and stable test environment
```

Última suíte completa:

```text
86 passed
5123 warnings
```

Os warnings são principalmente dívida técnica de compatibilidade/depreciação e serão tratados na etapa de limpeza.

---

# 8. Segurança JWT

## 8.1 Estado atual

```text
access token   30 minutos
refresh token   7 dias
```

O backend diferencia access e refresh tokens.

Access token não pode ser usado como refresh.

Refresh token não pode atuar como access.

Usuário inativo é rejeitado.

Empresa inativa é rejeitada em login e refresh.

Commit:

```text
fb7cf0a fix: harden authentication for inactive tenants
```

## 8.2 Rotação / revogação

Ao usar um refresh válido, o backend emite novo par de tokens.

Entretanto o refresh anterior não é revogado server-side.

Não existem atualmente:

- blacklist;
- `jti` persistido;
- token family;
- tabela de sessões;
- token version;
- detecção de reuse.

Classificação:

```text
Aceitável para MVP / portfólio com limitação documentada.
Recomendado endurecer antes de cenários comerciais mais sensíveis.
```

## 8.3 Armazenamento frontend

Os tokens permanecem no `localStorage`.

Isso aumenta impacto potencial de XSS.

Migração para cookie `HttpOnly` deve ser avaliada juntamente com:

- CORS com credentials;
- estratégia CSRF;
- sessão/revogação server-side;
- logout server-side.

Não fazer migração parcial.

## 8.4 Fila de refresh

Foi corrigido um problema no interceptor Axios.

Antes, se várias requisições aguardassem um refresh e a renovação falhasse, Promises poderiam permanecer pendentes.

Agora:

```text
refresh OK
→ libera fila

refresh falha
→ rejeita fila
→ limpa autenticação local
→ redireciona para login
```

Commit:

```text
1f51ec3 fix: handle refresh token queue failures
```

Validação após a alteração:

```text
npx tsc --noEmit  → OK
npm run build      → OK
npm audit          → 0 vulnerabilities
```

---

# 9. Segurança frontend e headers

Dependências frontend foram auditadas.

Estado final:

```text
npm audit              → 0 vulnerabilities
npm audit --omit=dev   → 0 vulnerabilities
```

Headers configurados na Vercel e confirmados em produção:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Strict-Transport-Security
Content-Security-Policy
```

## CSP e Zod

A CSP iniciou em modo `Report-Only`.

Durante a validação foi detectada execução de `Function(...)`. A origem principal identificada foi o mecanismo JIT do Zod 4.4.3.

Foi criado um wrapper central:

```ts
import { z } from 'zod'

z.config({
  jitless: true,
})

export { z }
```

Os imports diretos usados nas páginas de ordens passaram a utilizar esse wrapper.

Validações após a alteração:

```text
TypeScript             OK
Build Vite             OK
npm audit              0 vulnerabilities
unsafe-eval runtime    não reproduzido
```

A política foi então promovida para `Content-Security-Policy` bloqueante, sem adicionar `unsafe-eval`.

Fluxos validados em produção:

- login;
- dashboard;
- clientes;
- criação de cliente;
- ordens;
- criação de OS;
- detalhe da OS;
- inclusão de item;
- alteração de status.

Resultado:

```text
CSP bloqueante ativa
Aplicação funcional
Console sem violações CSP
```

## Decisão final sobre JWT no frontend

Os tokens permanecem no `localStorage`.

A ausência de revogação server-side, token family, `jti` persistido e logout server-side real permanece como limitação conhecida do MVP/portfólio.

Não foi criada uma rota `/logout` sem capacidade efetiva de revogação.

Antes de cenários comerciais mais sensíveis, a arquitetura de sessão deverá ser reavaliada de forma conjunta, incluindo cookie `HttpOnly`, CSRF, refresh server-side e revogação.

## Secrets e credenciais

Foi executada busca no Git por `SECRET_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL`, host Neon e URLs públicas.

Resultado:

- nenhuma credencial real do Neon foi encontrada versionada;
- nenhum host real `*.neon.tech` foi encontrado no Git;
- URLs públicas do Render aparecem apenas onde esperado;
- `.env.test` utiliza apenas valores locais/de teste;
- a `SECRET_KEY` de teste foi deixada explicitamente fictícia e não reutilizável em produção.

## Resultado da ETAPA 7

```text
JWT básico                      OK
Empresa inativa                 OK
Fila de refresh                 OK
Dependências                    OK
Headers                         OK
CSP bloqueante                  OK
Zod jitless                     OK
Credenciais produção no Git     NÃO ENCONTRADAS
localStorage                    LIMITAÇÃO DOCUMENTADA
Revogação server-side           ROADMAP
Logout server-side real         ROADMAP
```

**ETAPA 7 concluída para o escopo atual.**

---

# 10. Migração PostgreSQL Render → Neon — 20/08/2026

## Contexto

O PostgreSQL Free usado originalmente no Render expirou e foi suspenso.

Os registros existentes eram exclusivamente dados de teste.

Decisão:

```text
não preservar os dados antigos;
manter PostgreSQL;
trocar apenas o provedor de persistência.
```

## Novo provedor

```text
Neon Free
PostgreSQL
```

## Processo executado

1. Projeto criado no Neon.
2. Direct connection validada via `psql`.
3. Banco inicialmente confirmado vazio.
4. Variáveis temporárias configuradas no PowerShell.
5. Alembic conectado ao Neon.
6. Todas as migrations aplicadas.
7. Schema validado via `psql`.
8. Variáveis de produção atualizadas no Render.
9. Backend redeployado.
10. Health check validado.
11. CORS validado.
12. Operações reais executadas pelo frontend.
13. Dados confirmados diretamente no SQL Editor do Neon.

## Migrations aplicadas

```text
-> 06d5ab8065eb  initial_schema
-> 533015c239d4  expand_customer_address_fields
-> 885f034e93c2  order_number varchar to integer
-> 3e89efe30105  order_number unique per company
```

Revisão atual:

```text
3e89efe30105
```

## Tabelas confirmadas

```text
alembic_version
companies
customers
service_items
service_orders
subscriptions
users
```

## Validação de infraestrutura

Health:

```text
HTTP/1.1 200 OK
{"status":"ok"}
```

Preflight CORS:

```text
HTTP/1.1 200 OK
access-control-allow-origin: https://serviceflow-liard.vercel.app
access-control-allow-credentials: true
```

## Validação funcional pós-migração

Foi realizado pela aplicação publicada:

- registro/login;
- criação de empresa;
- criação de owner;
- criação de subscription;
- criação de cliente;
- criação de ordem;
- associação de técnico;
- inclusão de dois itens;
- transição da OS até `COMPLETED`;
- visualização no dashboard.

Consulta direta no Neon:

```text
companies        1
users            1
subscriptions    1
customers        1
service_orders   1
service_items    2
```

Resultado:

```text
MIGRAÇÃO CONCLUÍDA E VALIDADA
```

Arquitetura final:

```text
Frontend     Vercel
Backend      Render
Database     Neon PostgreSQL
Migrations   Alembic
```

Nenhuma alteração da arquitetura de domínio ou da camada ORM foi necessária.

---

# 11. Documentação

README e PROJECT foram sincronizados durante o hardening.

Commit anterior:

```text
5afaee7 docs: sync serviceflow technical documentation
```

Após a migração para Neon e o fechamento da ETAPA 7, os documentos registram:

- Neon como PostgreSQL de produção;
- 86 testes;
- CSP bloqueante;
- Zod em modo `jitless`;
- decisão sobre `localStorage`, refresh e logout;
- migração validada;
- limitações e roadmap atuais.

---

# 12. Dashboard

Status:

```text
IMPLEMENTADO COM LIMITAÇÃO
```

O frontend busca uma listagem limitada e calcula parte dos KPIs client-side.

Risco:

```text
mais de 50 OS
→ KPIs podem representar apenas parte da base
```

Recomendação para ETAPA 8:

- endpoints agregados no backend;
- filtros de período/status no servidor;
- KPIs calculados no banco;
- frontend apenas apresenta os agregados.

Não corrigido ainda.

---

# 13. Contrato da API de OS — pendências

Pontos identificados para revisão futura:

- alguns campos de schema ainda não possuem persistência equivalente;
- `technician_notes` precisa ser revisado;
- criação de OS com `items` precisa ser confirmada/alinhada;
- campos adicionais de equipamento/endereço precisam ser avaliados contra o model real.

Não apresentar esses campos como funcionalidades concluídas até validação.

---

# 14. Dívida técnica / limpeza

## Backend

- 5123 warnings na última suíte completa;
- depreciações Pydantic;
- warnings/depreciações pytest-asyncio em Python 3.14;
- warnings SlowAPI;
- dependências a revisar;
- possíveis duplicações em requirements.

## Frontend

- bundle principal acima de 500 kB;
- code splitting ainda não implementado;
- arquivos/componentes residuais precisam de revisão;
- `UsersPage` possui fluxo de erro que precisa ser revisado;
- acessibilidade ainda requer auditoria;
- estilos inline ainda existem em quantidade relevante.

---

# 15. CI

Status:

```text
NÃO IMPLEMENTADO
```

Planejado:

- GitHub Actions;
- pytest backend;
- TypeScript check;
- build frontend;
- npm audit conforme estratégia definida;
- eventualmente migration check.

---

# 16. Ordem de trabalho

Ordem de prioridade original:

```text
ETAPA 1   Auditoria                           CONCLUÍDA
ETAPA 2   order_number multi-tenant           CONCLUÍDA
ETAPA 3   HTTP 500 nos testes                 CONCLUÍDA
ETAPA 4   Escopo TECHNICIAN                   CONCLUÍDA
ETAPA 5   Estabilização da suíte              CONCLUÍDA
ETAPA 6   README / PROJECT                    CONCLUÍDA
ETAPA 7   Segurança e hardening               CONCLUÍDA
ETAPA 8   Dashboard / agregações              PRÓXIMA
ETAPA 9   Limpeza técnica                     PENDENTE
ETAPA 10  CI                                  PENDENTE
ETAPA 11  Revisão final para portfólio        PENDENTE
```

Evento adicional concluído durante ETAPA 7:

```text
Migração Render PostgreSQL → Neon             CONCLUÍDA
```

---

# 17. Próxima ação recomendada

Iniciar a ETAPA 8:

```text
auditar dashboard atual
↓
identificar KPIs e fontes
↓
criar agregações no backend
↓
adicionar testes
↓
ajustar frontend
↓
validar comportamento com volume superior ao limite atual de 50 OS
```

Não iniciar a ETAPA 9 antes de estabilizar o dashboard.

---

# 18. Definition of Done para o case

O projeto será considerado pronto para fechamento como case principal quando:

- aplicação funcionar em produção;
- migrations estiverem consistentes;
- model e banco estiverem alinhados;
- isolamento multi-tenant estiver testado;
- autorização estiver formalizada;
- README refletir o código real;
- documentação não apresentar roadmap como funcionalidade;
- dependências principais estiverem revisadas;
- build frontend estiver verde;
- suíte backend estiver verde;
- segurança e limitações estiverem documentadas;
- dashboard deixar de depender da limitação de 50 OS;
- limpeza técnica principal estiver concluída;
- CI estiver configurado ou sua ausência estiver explicitamente justificada;
- `SERVICEFLOW_PORTFOLIO_STATE.md` for gerado com somente informações comprovadas.

---

# 19. Validação atual resumida

```text
BACKEND
pytest -q
86 passed

FRONTEND
npx tsc --noEmit       OK
npm run build           OK
npm audit               0 vulnerabilities
npm audit --omit=dev    0 vulnerabilities

PRODUÇÃO
Frontend Vercel         OK
Backend Render          OK
GET /health             200 OK
CORS                    OK
Neon PostgreSQL         OK
Alembic                 3e89efe30105
CSP bloqueante          OK
Console CSP             sem violações nos fluxos validados
```

---

# 20. Commits recentes relevantes

```text
4e0dda4  fix: enforce service order tenant and technician scope
fb7cf0a  fix: harden authentication for inactive tenants
36f6d23  test: add plan limits and stable test environment
5afaee7  docs: sync serviceflow technical documentation
549be3a  chore: harden frontend dependencies and security headers
1f51ec3  fix: handle refresh token queue failures
```

---

# 21. Segurança de credenciais

Nunca inserir em documentação ou Git:

- senha real do Neon;
- connection string real;
- `POSTGRES_PASSWORD` de produção;
- `SECRET_KEY` de produção;
- tokens JWT;
- qualquer credencial de Render/Vercel/Neon.

Exemplos de variáveis devem utilizar placeholders.

---

# 22. Nota sobre `backend/.env.test`

`backend/.env.test` pertence somente ao ambiente automatizado de testes e deve conter exclusivamente credenciais locais/de teste.

Ele não deve ser alterado para apontar para:

- Neon de produção;
- Render;
- qualquer banco contendo dados reais.

Mudanças acidentais nesse arquivo durante configuração de produção devem ser revisadas antes de qualquer commit.
