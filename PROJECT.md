# ServiceFlow — Project Continuity Document

## Estado Atual

**Fase atual:** Hardening técnico e profissionalização para portfólio

**Última atualização:** 18/08/2026

**Status geral:** aplicação Full Stack funcional, publicada em produção e atualmente em processo de revisão técnica, fortalecimento dos testes, sincronização da documentação, segurança e preparação para apresentação como case profissional.

### Estado comprovado

```text
Backend FastAPI                  IMPLEMENTADO
Frontend React                   IMPLEMENTADO
PostgreSQL                       IMPLEMENTADO
Alembic                          IMPLEMENTADO
JWT                              IMPLEMENTADO
RBAC OWNER/ADMIN/TECHNICIAN      IMPLEMENTADO
RBAC VIEWER                      PARCIAL
Multi-tenancy                    IMPLEMENTADO
FSM de Ordens                    IMPLEMENTADO
Trial PRO                        IMPLEMENTADO
Downgrade FREE                   IMPLEMENTADO
Limites FREE                     IMPLEMENTADO
Dashboard                        IMPLEMENTADO COM LIMITAÇÃO
Deploy                           IMPLEMENTADO
Testes backend                   82 PASSANDO
CI                               NÃO IMPLEMENTADO
Revogação server-side JWT        NÃO IMPLEMENTADA
```

---

# URLs de Produção

* **Frontend:** https://serviceflow-liard.vercel.app
* **Backend:** https://serviceflow-backend-5ljk.onrender.com
* **Swagger:** https://serviceflow-backend-5ljk.onrender.com/docs

---

# 1. Contexto do Produto

O **ServiceFlow** é um SaaS B2B de Field Service Management voltado inicialmente para:

* técnicos autônomos;
* pequenas empresas;
* prestadores de serviços de refrigeração;
* empresas de manutenção de ar-condicionado.

O produto centraliza atividades como:

* clientes;
* técnicos;
* ordens de serviço;
* agendamento;
* prioridade;
* status;
* itens e peças;
* valores;
* acompanhamento operacional;
* planos e limites SaaS.

A arquitetura é multi-tenant: cada empresa representa um tenant independente.

---

# 2. Stack Atual

## Backend

* Python 3.14;
* FastAPI;
* SQLAlchemy 2 assíncrono;
* asyncpg;
* PostgreSQL;
* Alembic;
* Pydantic;
* pydantic-settings;
* JWT;
* passlib;
* bcrypt;
* pytest;
* pytest-asyncio;
* httpx.

## Frontend

* React 19;
* TypeScript;
* Vite;
* Tailwind CSS;
* shadcn/ui;
* TanStack Query;
* Zustand;
* React Hook Form;
* Zod;
* Axios;
* Recharts.

## Infraestrutura

* Render;
* Vercel;
* PostgreSQL gerenciado;
* Docker disponível para desenvolvimento e deploy;
* PostgreSQL local também suportado para desenvolvimento e testes.

---

# 3. Arquitetura Atual

O projeto utiliza um **monólito modular**, adequado ao porte atual do produto.

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

Não existe atualmente necessidade técnica que justifique migração para microservices.

---

# 4. Estrutura Principal

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
│   │   └── services/
│   │
│   ├── alembic/
│   │   └── versions/
│   │
│   ├── tests/
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
│   └── package.json
│
├── docker-compose.prod.yml
├── Caddyfile
├── README.md
└── PROJECT.md
```

---

# 5. Histórico Relevante — Pós-Deploy

## 5.1 Registro público

O backend já possuía:

```text
POST /api/v1/auth/register
```

mas inicialmente não existia tela pública de cadastro no frontend.

Foi implementada:

```text
/register
```

com:

* nome da empresa;
* nome do owner;
* e-mail;
* senha;
* login automático após cadastro;
* redirecionamento para o dashboard.

---

## 5.2 Correção das rotas SPA na Vercel

Rotas diretas como:

```text
/login
/register
/orders/{id}
```

retornavam `404` quando abertas diretamente.

Foi criado:

```text
frontend/vercel.json
```

com rewrite para:

```text
index.html
```

permitindo que o React Router controle as rotas da SPA.

---

# 6. Multi-tenancy e `order_number`

## Problema original

A primeira implementação utilizava unicidade global de:

```text
order_number
```

mesmo a geração do próximo número sendo feita por empresa.

Isso criava conflito quando diferentes empresas tentavam possuir:

```text
OS 1
```

A migration:

```text
3e89efe30105_order_number_unique_per_company.py
```

corrigiu o banco para:

```text
UNIQUE(company_id, order_number)
```

permitindo:

```text
Empresa A → OS 1
Empresa A → OS 2

Empresa B → OS 1
Empresa B → OS 2
```

---

## Hardening realizado em 18/08/2026

Durante a auditoria técnica foi identificado que a migration estava correta, porém o model ainda possuía:

```python
unique=True
```

diretamente em `order_number`.

Isso fazia o schema criado por:

```python
Base.metadata.create_all()
```

ser diferente do schema criado pelo Alembic.

O model foi corrigido para possuir explicitamente:

```text
UNIQUE(company_id, order_number)
```

e a unicidade global foi removida.

### Testes adicionados

Foram adicionados testes comprovando:

* duplicidade de `order_number` bloqueada dentro da mesma empresa;
* mesmo `order_number` permitido em empresas diferentes.

Resultado:

```text
2 passed
```

A suíte completa de ordens continuou verde após a alteração.

### Situação atual

```text
MODEL      = constraint por empresa
MIGRATION  = constraint por empresa
TESTES     = comprovam a regra
```

Nenhuma nova migration foi necessária, pois a migration existente já representava corretamente o schema desejado.

---

# 7. Geração de número de OS

A estratégia atual utiliza conceitualmente:

```text
MAX(order_number) + 1
```

filtrado por empresa.

Isso funciona no cenário atual, mas existe risco de concorrência:

```text
requisição A → próximo número = 21
requisição B → próximo número = 21
```

A constraint do PostgreSQL impede corrupção de dados, porém uma das requisições pode receber erro de integridade.

### Classificação

**MÉDIO**

### Recomendação MVP

Avaliar retry controlado em caso de conflito.

### Recomendação para escala

Avaliar:

* contador transacional por empresa;
* locking adequado no PostgreSQL;
* estratégia equivalente com garantia transacional.

Não é necessária arquitetura complexa neste estágio.

---

# 8. Testes que aceitavam HTTP 500

Durante a auditoria foram encontrados quatro testes contendo lógica equivalente a:

```python
assert response.status_code in (200, 500)
```

Isso permitia que falhas internas fossem interpretadas como testes válidos.

As ocorrências estavam em testes relacionados a:

* listagem de OS;
* técnico;
* paginação;
* isolamento multi-tenant.

Todos foram corrigidos para exigir explicitamente:

```text
HTTP 200
```

### Validação

Testes específicos:

```text
4 passed
```

Depois:

```text
23 passed
```

na suíte de ordens existente naquele momento.

Não existem mais aqueles contratos permitindo HTTP 500 como sucesso.

---

# 9. Rate Limiting e infraestrutura de testes

O ServiceFlow possui rate limiting em runtime.

Exemplos:

```text
registro → 5/minuto
login    → 10/minuto
```

Durante a execução da suíte completa, foi identificado que os testes compartilhavam o contador do limiter e começavam a receber:

```text
429 Rate limit exceeded
```

mesmo em testes que não tinham relação com rate limiting.

Foi corrigida a infraestrutura de testes para desabilitar o limiter durante a suíte geral.

### Importante

Essa alteração é restrita ao ambiente de testes.

O rate limiting continua ativo na aplicação em runtime.

Testes específicos de rate limiting podem reativá-lo quando essa cobertura for implementada.

---

# 10. Regra de acesso das OS

Durante a auditoria foi identificado comportamento inconsistente para `TECHNICIAN`.

Antes da correção:

```text
TECHNICIAN
├─ conseguia listar todas as OS da empresa
├─ conseguia acessar detalhes de outras OS
├─ update possuía proteção parcial
├─ itens possuíam proteção parcial
└─ change_status não aplicava a mesma regra
```

Foi definida formalmente a seguinte política:

## OWNER

Pode acessar todas as OS da própria empresa.

## ADMIN

Pode acessar todas as OS da própria empresa.

## TECHNICIAN

Pode acessar somente OS atribuídas a ele.

A regra é aplicada em:

* listagem;
* detalhes;
* atualização;
* mudança de status;
* listagem de itens;
* adição de itens;
* remoção de itens.

O técnico também não pode reatribuir sua própria OS para outro técnico.

---

## Centralização da regra

Foi adicionada lógica central na camada de service para evitar repetição de autorização em múltiplos endpoints.

A separação conceitual passou a ser:

```text
get_or_404()
→ garante isolamento por empresa

get_accessible_or_404()
→ garante isolamento por empresa
→ aplica regra do usuário
```

RBAC não foi transferido para o repository.

O repository permanece responsável por persistência e consultas.

---

## Testes adicionados

Foram adicionados testes para garantir que um técnico:

* lista apenas suas OS;
* não acessa OS de outro técnico;
* não altera status de OS de outro técnico;
* não lista itens de OS de outro técnico;
* não reatribui sua própria OS.

Resultado específico:

```text
5 passed
```

Suíte completa de ordens após a alteração:

```text
28 passed
```

---

# 11. RBAC

Existem atualmente atalhos de autorização como:

```python
AdminOnly

OwnerOnly

TechOrAbove
```

### Perfis considerados implementados

```text
OWNER
ADMIN
TECHNICIAN
```

### VIEWER

O enum:

```text
VIEWER
```

existe no domínio.

Porém ainda não existe política funcional suficientemente definida e testada para que o perfil seja considerado completo.

Status:

```text
VIEWER → PARCIALMENTE IMPLEMENTADO
```

### Roadmap

Antes de considerar `VIEWER` concluído:

1. definir quais recursos pode listar;
2. definir quais detalhes pode acessar;
3. confirmar que é read-only;
4. definir acesso ao dashboard;
5. criar testes específicos.

---

# 12. Máquina de Estados da OS

Estado atual:

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

Transições diferentes dessas são rejeitadas pela camada de serviço.

---

# 13. Planos e Trial

Foi definida a seguinte estratégia de produto:

```text
Novo tenant
       ↓
PRO
TRIALING
14 dias
       ↓
expiração
       ↓
FREE
ACTIVE
```

O usuário não é expulso do produto quando o trial termina.

Ele permanece ativo no plano Free.

---

## Limites FREE

| Recurso           | Limite |
| ----------------- | -----: |
| Técnicos          |      1 |
| Clientes          |      5 |
| Ordens de serviço | 10/mês |

Os demais planos ainda não possuem limites definitivos configurados.

---

# 14. Expiração do Trial

A expiração é atualmente verificada de forma:

```text
lazy / on-request
```

A cada requisição autenticada, a aplicação pode verificar se:

```text
status == TRIALING
```

e:

```text
trial_ends_at < agora
```

Caso positivo:

```text
plan_tier → FREE
status    → ACTIVE
```

Não existe atualmente worker ou cron dedicado ao downgrade.

Essa abordagem é considerada aceitável para o MVP.

---

# 15. Testes de Planos

Foi criado:

```text
backend/tests/test_plans.py
```

Os testes comprovam:

## Trial

* novo tenant inicia em PRO;
* status inicial é TRIALING;
* duração aproximada de 14 dias;
* trial expirado realiza downgrade;
* plano final passa para FREE;
* subscription passa para ACTIVE.

## FREE

* máximo de 1 técnico;
* máximo de 5 clientes;
* máximo de 10 OS por mês;
* criação excedente é bloqueada.

Resultado:

```text
5 passed
```

---

# 16. Usuário Inativo

Foram adicionados testes para dois cenários:

```text
usuário inativo tentando login
→ acesso bloqueado
```

e:

```text
usuário possuía access token
→ usuário é inativado
→ token deixa de dar acesso à aplicação
```

Resultado específico:

```text
2 passed
```

---

# 17. Estado Atual da Suíte

Antes do hardening:

```text
68 testes
```

Após as etapas de revisão e ampliação:

```text
82 passed
```

Cobertura funcional existente inclui:

* autenticação;
* login;
* token;
* refresh;
* usuário inativo;
* empresas;
* usuários;
* clientes;
* multi-tenancy;
* ordens;
* itens;
* máquina de estados;
* técnico atribuído;
* numeração por empresa;
* trial;
* downgrade;
* limites FREE.

A suíte backend encontra-se verde.

---

# 18. Warnings

A execução completa atual gera milhares de warnings.

Grande parte está relacionada a:

* APIs deprecated do Pydantic;
* `pytest-asyncio`;
* comportamento de `asyncio` depreciado no Python 3.14;
* dependências como SlowAPI.

Os warnings não estão sendo tratados durante as etapas funcionais para evitar misturar hardening de dependências com correções de regras de negócio.

Status:

```text
ROADMAP — limpeza técnica
```

---

# 19. Autenticação JWT

O sistema utiliza:

```text
access token
refresh token
```

O frontend persiste o estado de autenticação utilizando armazenamento local.

O Axios possui interceptor para:

1. enviar access token;
2. receber `401`;
3. solicitar refresh;
4. atualizar os tokens;
5. repetir a requisição original.

---

## Limitação atual do refresh

Apesar de um novo refresh token ser emitido, o backend não mantém atualmente:

* blacklist;
* token families;
* `jti` persistido;
* tabela de refresh tokens;
* revogação server-side.

Portanto, a emissão de um novo refresh token não invalida criptograficamente o anterior.

Não devemos descrever o comportamento atual como **refresh token rotation com revogação**.

Status:

```text
Aceitável para MVP
Hardening recomendado antes de exposição comercial mais ampla
```

---

# 20. Tokens no localStorage

O JWT armazenado no DevTools não é a `SECRET_KEY`.

É o próprio token assinado.

A `SECRET_KEY` deve existir exclusivamente no backend.

O principal trade-off do `localStorage` é exposição a XSS.

Como os tokens são enviados através do header:

```text
Authorization: Bearer ...
```

CSRF não é atualmente o risco central dessa implementação.

### Revisão futura

Avaliar:

* httpOnly cookies;
* refresh token server-side;
* CSP;
* redução da superfície de XSS;
* logout com revogação.

---

# 21. Segurança já implementada

Itens encontrados no código:

* JWT;
* hashing de senha;
* RBAC;
* multi-tenancy;
* rate limiting;
* security headers;
* CORS configurável;
* tratamento de exceções;
* validação Pydantic.

Portanto, `rate limiting` e `security headers` não devem permanecer documentados como recursos ausentes.

---

# 22. Segurança ainda pendente

## Médio / hardening

* armazenamento dos tokens no frontend;
* refresh token sem revogação;
* política de logout server-side;
* CSP;
* revisão de XSS;
* revisão de secrets;
* revisão de logs;
* mensagens de erro;
* política `VIEWER`.

## A revisar antes de exposição comercial maior

* revogação de sessão;
* estratégia de refresh token;
* política final de headers;
* auditoria de dependências;
* backups;
* rotação de secrets.

---

# 23. Dashboard

O dashboard atualmente busca aproximadamente:

```text
page_size = 50
```

ordens de serviço.

Parte dos KPIs e gráficos é calculada no frontend sobre essa coleção.

Consequentemente, quando existirem mais de 50 OS, indicadores podem deixar de representar o total real.

Status:

```text
IMPLEMENTADO COM LIMITAÇÃO
```

### Solução recomendada

Criar endpoints agregados no backend para:

* total de OS;
* status;
* receita;
* períodos;
* evolução mensal;
* indicadores relevantes.

As agregações devem ser executadas diretamente no PostgreSQL.

Isso será tratado em etapa específica.

---

# 24. Contrato da API de OS — pontos pendentes

Durante a auditoria foram identificados campos existentes nos schemas que não possuem persistência equivalente comprovada no model.

Exemplos encontrados:

```text
location_reference
equipment_type
equipment_brand
equipment_model
equipment_serial
```

Também foi identificado:

```text
technician_notes
```

como campo que precisa de revisão quanto à persistência.

Além disso, o schema de criação aceita:

```text
items
```

mas a criação inicial da OS precisa ser revisada para confirmar se esses itens são realmente processados.

Status:

```text
PARCIALMENTE IMPLEMENTADO / revisar contrato
```

Não apresentar esses campos como funcionalidades concluídas enquanto não forem alinhados entre:

```text
schema
service
model
migration
testes
```

---

# 25. Infraestrutura de Desenvolvimento

Durante o hardening foi comprovado que Docker não é obrigatório para executar a suíte.

Ambiente utilizado:

```text
Windows
Python 3.14.6
PostgreSQL 16.15
venv
pytest
```

Também continua existindo configuração Docker.

---

## Banco de testes

Foi criado banco isolado:

```text
serviceflow_test
```

O banco de testes deve permanecer completamente separado dos bancos:

```text
development
production
```

A suíte recria estruturas durante a execução.

Nunca apontar o `.env.test` para produção.

---

# 26. Divergência de Python

Situação encontrada:

```text
backend/Dockerfile
→ Python 3.12

backend/Dockerfile.prod
→ Python 3.14
```

Ambiente local validado:

```text
Python 3.14.6
```

Essa divergência ainda deve ser revisada.

Status:

```text
ROADMAP — alinhamento de infraestrutura
```

---

# 27. Dependências

Existem:

```text
requirements.txt
requirements.lock
```

O `requirements.lock` é atualmente a fonte mais adequada para reprodução exata do ambiente validado.

Foi identificada duplicação de dependências no `requirements.txt`.

Essa limpeza será feita posteriormente.

---

# 28. Deploy

## Frontend

Hospedado na Vercel.

## Backend

Hospedado no Render.

## Banco

PostgreSQL gerenciado.

## Migrations

Alembic utilizado para evolução do schema.

A configuração de deploy deve permanecer sincronizada com as migrations antes da revisão final para portfólio.

---

# 29. Situação das Etapas de Hardening

```text
ETAPA 1
Auditoria rápida da estrutura
✅ CONCLUÍDA

ETAPA 2
order_number + constraint multi-tenant
✅ CONCLUÍDA

ETAPA 3
Remoção de testes que aceitavam HTTP 500
✅ CONCLUÍDA

ETAPA 4
Regra de acesso das OS por TECHNICIAN
✅ CONCLUÍDA

ETAPA 5
Execução e estabilização dos testes
✅ CONCLUÍDA
82 testes verdes

ETAPA 6
README / PROJECT.md
🔄 EM ANDAMENTO

ETAPA 7
Segurança JWT
⏳ PRÓXIMA

ETAPA 8
Dashboard e agregações
⏳ PENDENTE

ETAPA 9
Limpeza técnica
⏳ PENDENTE

ETAPA 10
CI
⏳ PENDENTE

ETAPA 11
Revisão final para portfólio
⏳ PENDENTE
```

---

# 30. Roadmap Técnico Atual

## Segurança

* [ ] revisar armazenamento JWT;
* [ ] definir estratégia de refresh token;
* [ ] avaliar blacklist/token families;
* [ ] revisar CSP;
* [ ] revisar XSS;
* [ ] avaliar logout server-side;
* [ ] revisar mensagens de erro;
* [ ] revisar secrets e logs.

## Dashboard

* [ ] criar agregações no backend;
* [ ] remover KPIs dependentes de somente 50 registros.

## Banco

* [ ] revisar índices multi-tenant;
* [ ] endurecer geração concorrente de `order_number`.

## API

* [ ] alinhar schemas e persistência das OS;
* [ ] revisar `items` na criação;
* [ ] revisar `technician_notes`.

## RBAC

* [ ] definir política do `VIEWER`;
* [ ] criar testes após definição.

## Frontend

* [ ] corrigir usos incorretos de `toast.success` em tratamento de erro;
* [ ] revisar loading;
* [ ] revisar error states;
* [ ] revisar empty states;
* [ ] revisar acessibilidade;
* [ ] remover código residual;
* [ ] revisar componentes antigos;
* [ ] revisar code splitting.

## Infraestrutura

* [ ] alinhar versões Python;
* [ ] criar CI;
* [ ] executar backend tests em CI;
* [ ] executar TypeScript/build frontend em CI.

## Dependências e warnings

* [ ] revisar Pydantic deprecated API;
* [ ] revisar pytest-asyncio;
* [ ] revisar SlowAPI;
* [ ] revisar compatibilidade com Python 3.14;
* [ ] limpar `requirements.txt`.

---

# 31. Definition of Done para Portfólio

O ServiceFlow será considerado pronto para apresentação como case principal quando:

* [x] aplicação executa;
* [x] migrations principais funcionam;
* [x] `order_number` está alinhado ao tenant;
* [x] testes não aceitam 500 como sucesso;
* [x] regra de TECHNICIAN está definida;
* [x] isolamento multi-tenant possui testes;
* [x] planos e trial possuem testes;
* [x] suíte backend está verde;
* [ ] README e PROJECT.md totalmente sincronizados;
* [ ] revisão JWT concluída;
* [ ] dashboard corrigido;
* [ ] código residual revisado;
* [ ] frontend build novamente validado;
* [ ] CI implementada;
* [ ] limitações finais documentadas;
* [ ] `SERVICEFLOW_PORTFOLIO_STATE.md` gerado.

---

# 32. Próximo Passo

Após sincronizar `README.md` e `PROJECT.md`, iniciar:

```text
ETAPA 7 — Segurança JWT
```

A revisão deve abranger:

* access token;
* refresh token;
* localStorage;
* interceptors;
* expiração;
* renovação;
* logout;
* revogação;
* XSS;
* CSRF quando aplicável;
* CORS;
* headers;
* CSP;
* secrets;
* logs.

Não tratar `localStorage` automaticamente como vulnerabilidade crítica.

A classificação deverá considerar o contexto real do MVP e distinguir:

```text
aceitável para MVP
melhoria recomendada
necessário antes de produção comercial
```

---

# 33. Documento Final Planejado

Ao término de todas as etapas será criado:

```text
SERVICEFLOW_PORTFOLIO_STATE.md
```

O documento deverá conter exclusivamente informações comprovadas sobre:

* problema;
* solução;
* stack;
* arquitetura;
* funcionalidades;
* regras de negócio;
* autenticação;
* RBAC;
* multi-tenancy;
* testes;
* deploy;
* segurança;
* status;
* limitações;
* roadmap;
* principais decisões de engenharia.

Esse documento será utilizado como fonte confiável para construção e atualização do case profissional do ServiceFlow no portfólio.
