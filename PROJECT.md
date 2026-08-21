# ServiceFlow — Project Continuity Document

## Sessão atual

**Data de referência:** 21/08/2026
**Fase:** hardening, dashboard, limpeza técnica e CI concluídos; próxima fase: revisão final para portfólio.
**Status:** aplicação publicada e funcional, com frontend na Vercel, backend no Render e PostgreSQL no Neon. A suíte backend possui 90 testes aprovados. O frontend está com TypeScript, build, auditoria de dependências, CSP bloqueante e code splitting validados. O GitHub Actions executa CI de backend e frontend com sucesso.

### URLs de produção

- **Frontend:** https://serviceflow-liard.vercel.app
- **Backend:** https://serviceflow-backend-5ljk.onrender.com
- **Swagger:** https://serviceflow-backend-5ljk.onrender.com/docs
- **Health:** https://serviceflow-backend-5ljk.onrender.com/health

---

# 1. Objetivo do projeto

O ServiceFlow é um SaaS B2B de Field Service Management voltado inicialmente para técnicos autônomos e pequenas empresas de refrigeração e ar-condicionado.

O projeto é utilizado como case de portfólio Full Stack.

A prioridade nesta fase é manter consistência entre código, testes, migrations e documentação, com foco em:

- isolamento multi-tenant;
- autorização e RBAC;
- regras de negócio;
- segurança;
- qualidade da suíte;
- arquitetura;
- infraestrutura;
- observabilidade básica por health check;
- CI;
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
- pytest 9.1.1;
- pytest-asyncio 1.4.0;
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
- Recharts;
- React Router.

## Infraestrutura

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

## Validação local mais recente

```text
Windows
Python 3.14.6
pytest 9.1.1
pytest-asyncio 1.4.0
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

A arquitetura continua adequada ao porte e ao estágio atual. Não há justificativa técnica para microservices neste momento.

---

# 4. Estado funcional comprovado

```text
Backend FastAPI                     IMPLEMENTADO
Frontend React                      IMPLEMENTADO
PostgreSQL                          IMPLEMENTADO
Alembic                             IMPLEMENTADO
JWT                                 IMPLEMENTADO
RBAC OWNER/ADMIN/TECHNICIAN         IMPLEMENTADO
RBAC VIEWER                         PARCIALMENTE IMPLEMENTADO
Multi-tenancy                       IMPLEMENTADO
FSM de Ordens                       IMPLEMENTADO
Trial PRO                           IMPLEMENTADO
Downgrade FREE                      IMPLEMENTADO
Limites FREE                        IMPLEMENTADO
Dashboard agregado                  IMPLEMENTADO
Deploy                              IMPLEMENTADO
Security headers                    IMPLEMENTADO
CSP bloqueante                      IMPLEMENTADO
Code splitting por rota             IMPLEMENTADO
CI GitHub Actions                   IMPLEMENTADO
Revogação server-side JWT           NÃO IMPLEMENTADA
```

---

# 5. Regras de negócio confirmadas

## 5.1 Numeração das ordens

A unicidade é definida por:

```text
(company_id, order_number)
```

É permitido:

```text
Empresa A → OS 1
Empresa B → OS 1
```

Não é permitido duplicar o mesmo `order_number` dentro da mesma empresa.

A geração atual utiliza `MAX(order_number) + 1` por empresa.

**Risco conhecido:** concorrência simultânea pode gerar colisão. A constraint preserva a integridade do banco, mas uma requisição concorrente pode falhar. Hardening futuro recomendado.

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

O enum existe no domínio, porém a política funcional específica ainda não foi formalizada integralmente.

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

Principais achados originais:

- drift entre model e migration de `order_number`;
- testes aceitando HTTP 500;
- regra TECHNICIAN inconsistente;
- divergências entre documentação e código;
- risco de concorrência em numeração;
- limitações JWT;
- dashboard limitado a 50 registros;
- itens residuais no frontend;
- política VIEWER incompleta.

## ETAPA 2 — `order_number` multi-tenant

Concluída.

- removida unicidade global;
- adicionada `UniqueConstraint("company_id", "order_number")`;
- model alinhado à migration;
- testes de duplicidade no mesmo tenant;
- testes permitindo mesmo número em tenants diferentes.

Migration:

```text
3e89efe30105
order_number unique per company
```

## ETAPA 3 — HTTP 500 nos testes

Concluída.

Os asserts que aceitavam `(200, 500)` foram substituídos pelos contratos HTTP esperados.

## ETAPA 4 — acesso TECHNICIAN

Concluída.

```text
OWNER / ADMIN → todas as OS do tenant
TECHNICIAN    → apenas OS atribuídas a ele
```

Cobertura adicionada para listagem, detalhe, status, itens e tentativa de reatribuição.

## ETAPA 5 — estabilização da suíte

Concluída.

O rate limiter permanece ativo em runtime e é desabilitado na suíte geral para evitar interferência de contadores globais entre testes não relacionados ao rate limiting.

Cobertura inclui:

- usuário inativo;
- empresa inativa;
- trial;
- downgrade;
- limites FREE.

Estado atual:

```text
90 passed
2 warnings
```

Os dois warnings restantes são de depreciação originados no SlowAPI sob Python 3.14. Não são mascarados.

---

# 8. Segurança JWT

## 8.1 Estado atual

```text
access token   30 minutos
refresh token   7 dias
```

O backend diferencia access e refresh tokens.

- access token não pode ser usado como refresh;
- refresh token não pode atuar como access;
- usuário inativo é rejeitado;
- empresa inativa é rejeitada em login e refresh.

## 8.2 Rotação / revogação

Ao usar um refresh válido, o backend emite novo par de tokens.

O refresh anterior não é revogado server-side.

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

Isso aumenta o impacto potencial de XSS.

Uma eventual migração para cookie `HttpOnly` deve ser tratada em conjunto com CORS com credentials, estratégia CSRF, sessão/revogação server-side e logout server-side real.

## 8.4 Fila de refresh

O interceptor Axios trata concorrência de refresh:

```text
refresh OK
→ libera fila

refresh falha
→ rejeita fila
→ limpa autenticação local
→ redireciona para login
```

---

# 9. Segurança frontend e headers

Auditorias atuais:

```text
npm audit              → 0 vulnerabilities
npm audit --omit=dev   → 0 vulnerabilities
```

Headers configurados e validados em produção:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Strict-Transport-Security
Content-Security-Policy
```

## CSP e Zod

A CSP está ativa em modo bloqueante e sem `unsafe-eval`.

O Zod utiliza wrapper central com modo `jitless`:

```ts
import { z } from 'zod'

z.config({
  jitless: true,
})

export { z }
```

Fluxos validados em produção incluem login, dashboard, clientes, criação de cliente, ordens, criação de OS, detalhe da OS, inclusão de item e alteração de status.

O `'unsafe-inline'` permanece temporariamente em `style-src`.

## Secrets

Foi executada busca por credenciais versionadas.

Resultado confirmado:

- nenhuma credencial real do Neon encontrada no Git;
- nenhum host real `*.neon.tech` encontrado no Git;
- `.env.test` contém somente valores locais/de teste;
- `SECRET_KEY` de teste é explicitamente fictícia.

---

# 10. PostgreSQL de produção — Neon

O PostgreSQL gratuito originalmente utilizado no Render expirou e foi substituído por Neon em 20/08/2026.

Como os registros existentes eram apenas dados de teste, não houve necessidade de preservar os dados.

Migrations aplicadas:

```text
06d5ab8065eb  initial_schema
533015c239d4  expand_customer_address_fields
885f034e93c2  order_number varchar to integer
3e89efe30105  order_number unique per company
```

Revisão atual:

```text
3e89efe30105
```

Tabelas confirmadas:

```text
alembic_version
companies
customers
service_items
service_orders
subscriptions
users
```

Arquitetura final:

```text
Frontend     Vercel
Backend      Render
Database     Neon PostgreSQL
Migrations   Alembic
```

---

# 11. Dashboard e agregações

## ETAPA 8 — concluída

O problema original era o cálculo client-side sobre uma listagem limitada a 50 ordens.

A solução atual utiliza:

```text
GET /api/v1/dashboard/summary
```

O backend agrega:

- contagem por status;
- ordens por mês nos últimos seis meses;
- oito ordens recentes.

Escopo de autorização:

```text
OWNER / ADMIN → dados de todo o tenant
TECHNICIAN    → apenas OS atribuídas ao próprio técnico
```

O backend preenche meses sem ordens com zero.

Foram adicionados testes para:

- volume superior a 50 ordens;
- dashboard vazio;
- isolamento entre tenants;
- escopo TECHNICIAN.

A limitação de 50 ordens não existe mais no cálculo do dashboard.

---

# 12. Contrato da API de OS — pendências

Pontos ainda classificados como dívida técnica/roadmap:

- revisar campos de schema sem persistência equivalente;
- revisar `technician_notes`;
- revisar criação de OS com `items`;
- avaliar campos adicionais de equipamento/endereço contra o model real.

Não apresentar esses pontos como funcionalidades concluídas sem validação.

---

# 13. Limpeza técnica

## ETAPA 9 — concluída para o escopo atual

### Backend

- configuração Pydantic migrada para `SettingsConfigDict`;
- `pytest-asyncio` atualizado para compatibilidade com Python 3.14;
- `pytest` alinhado em `9.1.1`;
- suíte reduzida de milhares de warnings para apenas 2 warnings externos do SlowAPI;
- `pip check` sem dependências quebradas.

### Frontend

- arquivo residual vazio removido;
- feedbacks de erro corrigidos;
- busca por `console.log`, `console.debug`, `breakpoint` e `pdb` sem resíduos;
- encoding UTF-8 verificado sem mojibake real;
- code splitting por rota implementado com `React.lazy` e `Suspense`.

Build após code splitting:

```text
Bundle principal antes:  ~1.060,76 kB
Bundle principal depois: ~351,61 kB
gzip principal:          ~109,32 kB
DashboardPage:           ~357,73 kB
```

Redução aproximada do JavaScript inicial: 67%.

Nenhum chunk acima de 500 kB no build validado.

---

# 14. CI

## ETAPA 10 — concluída

Workflow:

```text
.github/workflows/ci.yml
```

Disparos:

- push para `main`;
- pull request para `main`;
- execução manual.

### Backend CI

```text
Ubuntu
Python 3.14
PostgreSQL 16 descartável
requirements.lock
pip check
Alembic upgrade head
pytest -q
```

Resultado validado:

```text
Backend ✅
90 testes aprovados
```

### Frontend CI

```text
Ubuntu
Node 24
npm ci
TypeScript check
Vite build
npm audit
npm audit --omit=dev
```

Resultado validado:

```text
Frontend ✅
0 vulnerabilidades
```

O CI não utiliza Neon, Render ou credenciais de produção.

---

# 15. Ordem de trabalho

```text
ETAPA 1   Auditoria                           CONCLUÍDA
ETAPA 2   order_number multi-tenant           CONCLUÍDA
ETAPA 3   HTTP 500 nos testes                 CONCLUÍDA
ETAPA 4   Escopo TECHNICIAN                   CONCLUÍDA
ETAPA 5   Estabilização da suíte              CONCLUÍDA
ETAPA 6   README / PROJECT                    CONCLUÍDA
ETAPA 7   Segurança e hardening               CONCLUÍDA
ETAPA 8   Dashboard / agregações              CONCLUÍDA
ETAPA 9   Limpeza técnica                     CONCLUÍDA
ETAPA 10  CI                                  CONCLUÍDA
ETAPA 11  Revisão final para portfólio        EM ANDAMENTO
```

Evento adicional:

```text
Migração Render PostgreSQL → Neon            CONCLUÍDA
```

---

# 16. Definition of Done para o case

Estado atual:

- [x] aplicação funciona em produção;
- [x] migrations consistentes;
- [x] model e banco alinhados para `order_number`;
- [x] isolamento multi-tenant testado;
- [x] autorização de OS formalizada;
- [x] dependências principais revisadas;
- [x] build frontend verde;
- [x] suíte backend verde;
- [x] segurança e limitações documentadas;
- [x] dashboard sem limitação de 50 OS;
- [x] limpeza técnica principal concluída;
- [x] CI configurado e validado;
- [ ] README e PROJECT atualizados com o estado final;
- [ ] `SERVICEFLOW_PORTFOLIO_STATE.md` gerado com somente informações comprovadas.

---

# 17. Validação atual resumida

```text
BACKEND
pytest -q
90 passed, 2 warnings

python -m pip check
No broken requirements found.

FRONTEND
npx --no-install tsc --noEmit   OK
npm run build                   OK
npm audit                       0 vulnerabilities
npm audit --omit=dev            0 vulnerabilities

BUILD
index principal                 ~351,61 kB
gzip principal                  ~109,32 kB
DashboardPage                   ~357,73 kB
chunks > 500 kB                 nenhum

CI
Backend                         VERDE
Frontend                        VERDE

PRODUÇÃO
Frontend Vercel                 OK
Backend Render                  OK
GET /health                     200 OK
CORS                            OK
Neon PostgreSQL                 OK
Alembic                         3e89efe30105
CSP bloqueante                  OK
```

---

# 18. Roadmap / limitações conhecidas

## Segurança

- revogação server-side de refresh token;
- blacklist / `jti` / token family;
- logout server-side real;
- avaliar cookie `HttpOnly` + CSRF;
- reduzir `style-src 'unsafe-inline'`.

## Banco

- endurecer geração concorrente de `order_number`;
- revisar índices multi-tenant quando houver carga real.

## RBAC

- formalizar política do `VIEWER`;
- adicionar testes após definição.

## API de ordens

- revisar campos de schema sem persistência equivalente;
- revisar `technician_notes`;
- revisar criação com `items`;
- revisar campos adicionais de equipamento/endereço.

## Qualidade

- acompanhar compatibilidade futura do SlowAPI com Python 3.14;
- auditoria específica de acessibilidade;
- otimizações adicionais de bundle apenas se métricas reais justificarem.

---

# 19. Próxima ação

Finalizar a ETAPA 11:

```text
revisar README público
↓
sincronizar PROJECT
↓
validar Git
↓
gerar SERVICEFLOW_PORTFOLIO_STATE.md
↓
revisão final do case
```

---

# 20. Segurança de credenciais

Nunca inserir em documentação ou Git:

- senha real do Neon;
- connection string real;
- `POSTGRES_PASSWORD` de produção;
- `SECRET_KEY` de produção;
- tokens JWT;
- credenciais de Render/Vercel/Neon.

Exemplos de variáveis devem utilizar placeholders.

`backend/.env.test` pertence exclusivamente ao ambiente automatizado/local de testes e não deve apontar para produção.
