# ServiceFlow — Project Continuity Document

## Sessão Atual
**Fase:** 3 — Pós-Deploy: correções, novas funcionalidades e lógica de negócio
**Status:** Sistema em produção, estável, com registro público de novas empresas funcionando, bug crítico de multi-tenant corrigido, e lógica completa de planos/trial implementada (backend + frontend). Próximo tema (nova conversa): auditoria de segurança.

## URLs de Produção
- **Frontend:** https://serviceflow-liard.vercel.app
- **Backend:** https://serviceflow-backend-5ljk.onrender.com
- **Docs/Swagger:** https://serviceflow-backend-5ljk.onrender.com/docs

---

## Sessão Fase 3.8 — Registro público, bug multi-tenant crítico, lógica de planos (17–18/07/2026)

### 1. Tela de registro público (`/register`) — não existia

Descoberta ao tentar liberar acesso a um terceiro: o backend já tinha `POST /api/v1/auth/register` desde a Fase 1, mas **nunca existiu tela de cadastro no frontend** — só era possível criar empresas via Swagger. Implementado:
- `authApi.register` adicionado em `src/api/auth.ts`, usando o tipo `components['schemas']['CompanyCreate']` gerado pelo `openapi-typescript`.
- `src/pages/RegisterPage.tsx` criada do zero, replicando o visual da `LoginPage` (painel escuro com branding + formulário), com campos: nome da empresa, nome do owner, e-mail, senha (mínimo 8 caracteres).
- Rota `/register` adicionada em `src/router/index.tsx`; link "Criar conta" adicionado na `LoginPage`.
- Registro bem-sucedido loga automaticamente e redireciona para o Dashboard.

### 2. Bug crítico: rotas diretas da SPA retornavam 404 na Vercel

Ao testar `/login` e `/register` acessando a URL diretamente (não via navegação client-side), a Vercel retornava `404: NOT_FOUND`. Causa: aplicações SPA servidas como arquivos estáticos precisam de configuração explícita dizendo ao host para redirecionar qualquer rota não encontrada para `index.html` (o React Router decide o resto no navegador). Sem isso, qualquer link direto, F5, ou compartilhamento de URL quebra.

**Correção:** criado `frontend/vercel.json`:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```
Resolve para **qualquer** rota do app (`/login`, `/register`, `/orders/123`, etc.), não só as testadas.

### 3. Bug crítico: `order_number` com unicidade GLOBAL em vez de por empresa

Ao testar o registro com uma segunda empresa e criar a primeira OS dela, ocorreu `500 Internal Server Error` (aparecendo no navegador como falso-positivo de bloqueio de CORS, já que respostas 500 não carregam headers de CORS). Log real do Render revelou:
```
IntegrityError: duplicate key value violates unique constraint "ix_service_orders_order_number"
DETAIL: Key (order_number)=(1) already exists.
```

**Causa raiz:** a migration original (`06d5ab8065eb_initial_schema`) criou o índice de `order_number` como **único em toda a tabela**, não por empresa — mas a lógica de geração (`get_next_order_number`) sempre calculava o próximo número **só dentro da empresa atual**. Resultado: a primeira empresa a criar uma OS "trancava" o número `1` para sempre; nenhuma outra empresa conseguia ter sua própria OS `#1`. Isso só apareceu com múltiplas empresas reais coexistindo — não aparecia nos testes anteriores, feitos com uma única empresa.

**Correção:** nova migration `3e89efe30105` (`order_number unique per company`), aplicada em dev e produção:
```python
def upgrade():
    op.drop_index(op.f('ix_service_orders_order_number'), table_name='service_orders')
    op.create_index('ix_service_orders_order_number', 'service_orders', ['order_number'], unique=False)
    op.create_unique_constraint(
        'uq_service_orders_company_order_number', 'service_orders', ['company_id', 'order_number']
    )
```
Agora `order_number` é único apenas dentro de `(company_id, order_number)` — cada empresa tem sua própria sequência começando do 1.

**Validado em produção**, incluindo teste real via celular: segunda empresa ("Teste Frio") criou sua OS `#1` com sucesso.

### 4. Lógica de planos e trial de 14 dias — decisão de produto + implementação completa

Decisão de produto (adotando prática comum de SaaS B2B para maximizar conversão): trial dá acesso **nível Pro completo** por 14 dias; ao expirar sem upgrade, a empresa faz **downgrade automático e permanente para o Free** (não bloqueio total) — mantendo a empresa ativa no produto em vez de expulsá-la, com limites reais:

| Recurso | Limite no Free |
|---|---|
| Técnicos | 1 |
| OS por mês | 10 |
| Clientes cadastrados | 5 |
| Básico / Pro / Empresa | Sem limites definidos ainda (todos `None` = ilimitado por ora) |

**Implementação backend:**
- `auth_service.py`: `register()` agora cria `company.plan_tier` e `subscription.plan_tier` como `PRO` (não `FREE`), mantendo `status=TRIALING` e `trial_ends_at = now + 14 dias`.
- `dependencies.py`: nova função `_apply_trial_expiration()`, chamada dentro de `get_current_user()` a cada requisição autenticada (checagem "preguiçosa", sem necessidade de cron job — importante porque o Render free tier não oferece workers agendados facilmente). Se `trial_ends_at` já passou e `status == TRIALING`, faz downgrade para `plan_tier=FREE`, `status=ACTIVE`, com commit imediato.
- `app/core/plan_limits.py` (novo arquivo): dicionário `PLAN_LIMITS` central; funções de contagem (`count_customers`, `count_technicians`, `count_orders_this_month`) reaproveitadas tanto pelas funções de checagem (`check_customer_limit`, `check_technician_limit`, `check_order_limit`, que lançam `403` ao atingir o limite) quanto pelo novo endpoint de uso.
- Checagens plugadas nos três endpoints de criação: `POST /customers`, `POST /users` (só quando `role == technician`), `POST /orders`.
- Novo endpoint `GET /companies/me/usage` retornando uso atual vs. limite de cada recurso (`PlanUsageResponse`).
- `Company` ganhou duas `@property` (`subscription_status`, `trial_ends_at`) que delegam para `company.subscription`, permitindo que `CompanyResponse` exponha esses campos sem duplicar dados nem exigir mudança no endpoint `/companies/me` (Pydantic lê via `getattr` automaticamente).

**Bug corrigido durante a implementação:** o `CompanyResponse` original não incluía `subscription_status` nem `trial_ends_at` — e o frontend antigo lia `company.subscription_plan` (nome que nunca existiu; o campo real sempre foi `plan_tier`). Isso fazia a seção "Assinatura" da tela de Configurações aparecer com "Plano atual" vazio.

**Implementação frontend:**
- `src/hooks/useCompany.ts`: interface `Company` corrigida (`plan_tier`, `subscription_status`, `trial_ends_at`); novo hook `usePlanUsage()` consumindo `/companies/me/usage`.
- `src/pages/SettingsPage.tsx`, seção `SubscriptionSection` reescrita: labels corrigidos para bater com o enum real do backend (`basico`/`empresa` em português, não `basic`/`enterprise`); exibe contagem de dias restantes do trial; barras de progresso de uso (técnicos, OS do mês, clientes) com destaque visual quando o limite é atingido; card do plano atual destacado visualmente entre os 4 disponíveis; botão "Solicitar upgrade via WhatsApp" (link `wa.me` com mensagem pré-preenchida).
- **Nota de troubleshooting para sessões futuras:** um link `<a>` com múltiplos atributos multi-linha quebrou repetidamente ao ser colado/editado no VS Code (perda do `<a` de abertura, ou `>` fechando cedo demais). A correção definitiva foi trocar por um `<button onClick={() => window.open(...)}>` em linha única — mais resistente a esse tipo de erro de edição.

### 5. Ajustes visuais menores

- Campo "Agendamento" (`datetime-local`) no modal de criar OS: navegadores mobile não mostram nenhuma pista visual de que é um campo de data (diferente do desktop, que renderiza a máscara nativa `dd/mm/aaaa --:--`). Adicionado texto de apoio fixo abaixo do campo ("selecionar data e hora"), já que o `placeholder` nativo não é suportado por esse tipo de input em nenhum navegador.
- Confirmado que não havia inconsistência real de largura entre os campos do formulário de OS — `CustomSelect` já herdava `fieldStyle` via spread; a percepção de desalinhamento provavelmente veio da renderização nativa do calendário do `datetime-local`, não do CSS.

---

## Fase 3 — Checklist (atualizado)

- [x] Backend + Frontend + Banco em produção (Render + Vercel)
- [x] Fluxo completo validado (login, cliente, OS, itens)
- [x] Registro público de novas empresas (`/register`)
- [x] Rewrites SPA configurados (`vercel.json`) — rotas diretas não quebram mais
- [x] Bug crítico de `order_number` global corrigido — multi-tenant real validado
- [x] Lógica de trial (14 dias, nível Pro) com downgrade automático para Free
- [x] Limites por plano (técnicos, OS/mês, clientes) implementados e validados (68/68 testes)
- [x] Tela de Configurações exibindo plano, status, dias de trial, uso vs. limite
- [x] Botão de solicitação de upgrade via WhatsApp

## Próximo Passo Recomendado

**Nova conversa dedicada: auditoria de segurança.**

Gatilho: usuário notou que aparece uma chave no Application → Local Storage do DevTools. Nota importante: isso é esperado para o `accessToken` JWT em si, que fica no `localStorage` por design da aplicação — mas vale confirmar na próxima sessão que a `SECRET_KEY` do backend (usada para *assinar* os tokens) nunca é exposta ao cliente; o que provavelmente foi visto é o próprio JWT assinado, não a chave secreta do servidor. Pontos a revisar:
- Armazenamento do JWT em `localStorage` (vulnerável a XSS) vs. alternativas como `httpOnly cookies`
- Rotação e blacklist de refresh tokens (já listado como pendência desde a Fase 1)
- Rate limiting nos endpoints de auth (login, register) contra força bruta
- Validação de CORS mais restritiva em produção
- Revisão de headers de segurança (CSP, HSTS, X-Frame-Options) — hoje dependentes só dos padrões do Render/Vercel
- Exposição de informações sensíveis em mensagens de erro (ex: enumeração de e-mails já cadastrados no registro)
- Revisão de permissões RBAC nos endpoints críticos
- Backup e rotação da `SECRET_KEY` de produção

## Decisões Pendentes / A Revisar (herdadas + novas desta sessão)
- Refatorar `OrdersPage.tsx` para shadcn `<Table>`; buscar `console.log` residuais; testar `UsersPage` como técnico; code-splitting por rota; simplificar login eliminando `/auth/me` extra; Service Worker fantasma em `localhost:5173`; migrar páginas de `style={{}}` inline para Tailwind puro.
- Investigar causa raiz do Pre-Deploy Command do Render não ter rodado no primeiro deploy (contornado com migration manual desde então, incluindo a mais recente).
- Monitorar prazo de 90 dias do PostgreSQL gratuito do Render.
- Avaliar migração para Hetzner quando houver clientes pagantes reais.
- **Novo:** definir limites reais para os planos Básico/Pro/Empresa (hoje todos ilimitados — só o Free tem limites definidos: 1 técnico, 10 OS/mês, 5 clientes).
- **Novo:** implementar upgrade self-service (hoje é 100% manual — UPDATE direto no banco após combinar pagamento por fora).
- **Novo:** revisar mensagens de erro do backend para não vazar informação (ex: "E-mail já cadastrado" no registro permite enumerar contas existentes).