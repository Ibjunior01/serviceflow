# ServiceFlow — Project Continuity Document

## Sessão Atual
**Fase:** 3 — Deploy em Produção **CONCLUÍDO**
**Status:** ServiceFlow está no ar, publicamente acessível, com banco de dados real, backend e frontend em produção. Fluxo completo validado em produção: login, criar cliente, criar OS, adicionar itens (peças/serviços), alterar status via FSM, dashboard com métricas e gráfico mensal. Suíte pytest (68/68) validada localmente como checkpoint final.

**Mudança de infraestrutura em relação ao plano original:** o deploy não foi feito no Hetzner (VPS pago) como planejado inicialmente — por decisão de custo, optou-se por hospedagem gratuita: **Render** (backend + PostgreSQL) e **Vercel** (frontend), ambos no free tier. Documentado abaixo com as limitações conhecidas dessa escolha.

## URLs de Produção
- **Frontend:** https://serviceflow-liard.vercel.app
- **Backend:** https://serviceflow-backend-5ljk.onrender.com
- **Docs/Swagger:** https://serviceflow-backend-5ljk.onrender.com/docs
- **Banco de dados:** PostgreSQL gerenciado pelo Render (`serviceflow-db`, região Oregon)

## Progresso das Fases

| Fase | Descrição | Status |
|------|-----------|--------|
| 1A–1G | Backend completo (estrutura, models, schemas, auth, CRUD, endpoints, testes) | ✅ Concluída |
| 2A | Frontend React + Vite + Tailwind — todas as telas | ✅ Concluída |
| 2B | Polimento de UX + Preparação para Deploy | ✅ Concluída |
| 3 | Deploy — Backend (Render) + Frontend (Vercel) | ✅ **Concluída — sistema em produção e funcional** |

## Decisões de Arquitetura (backend) — inalteradas desde sessões anteriores
- Async engine (asyncpg), API versionada em `/api/v1`, Settings via pydantic-settings com validação no boot
- UUID v4 como PK, `lazy="selectin"` obrigatório em relationships async, `ondelete` explícito em FKs
- Repository Pattern (`CRUDBase` genérico) + Service Layer, singletons de módulo
- `technician_id` (não `assigned_to`) em todas as camadas; `order_number` é `INTEGER` puro no banco, formatação `OS-0001` só no frontend
- Login via JSON `{"email", "password"}`; refresh sem blacklist no MVP
- **Enum `OrderStatus` (fonte da verdade, backend):** `draft`, `scheduled`, `in_progress`, `completed`, `invoiced`, `cancelled` — **não existe** (e nunca deveria ter existido no frontend) o status `assigned`, que foi removido nesta sessão (ver abaixo).

---

## Sessão Fase 3.7 — Deploy real em produção (16/07/2026)

Sessão que levou o ServiceFlow do ambiente local/simulado para produção pública de verdade, com múltiplos bugs de infraestrutura e um bug funcional relevante corrigidos ao longo do caminho.

### 1. Decisão de infraestrutura: Render + Vercel (grátis) em vez de Hetzner (pago)

Motivo: validar o deploy real antes de comprometer orçamento. Render oferece PostgreSQL e Web Service (Docker) gratuitos; Vercel já era gratuito para o frontend desde o início do planejamento.

**Limitações conhecidas do free tier, documentadas para decisão futura:**
- Web Service do Render **hiberna após inatividade** — primeira requisição após período ocioso tem latência maior (cold start) enquanto o container reinicia.
- PostgreSQL gratuito do Render **expira em 90 dias** salvo upgrade — ação necessária antes desse prazo se o projeto continuar nesse tier.
- Shell interativo do Render (útil para debug/comandos manuais) é recurso pago — indisponível no free tier.

### 2. Criação da infraestrutura Render

- **PostgreSQL** (`serviceflow-db`, Oregon) criado primeiro.
- **Web Service** (`serviceflow-backend`) criado apontando para `backend/Dockerfile.prod`:
  - Root Directory: `backend`
  - Docker Build Context: `backend`
  - Dockerfile Path: `backend/Dockerfile.prod`
  - Health Check Path: `/health` (endpoint já existente no `main.py`)
  - Pre-Deploy Command: `alembic upgrade head`
  - Instance Type: Free
- **Caddy não é necessário no Render** — a plataforma já provê HTTPS/proxy reverso automaticamente; o serviço `caddy` do `docker-compose.prod.yml` (pensado para Hetzner) não se aplica aqui.

### 3. Bug: frontend não sabia a URL da API em produção

`src/api/client.ts` tinha `baseURL: '/api/v1'` hardcoded, dependente do proxy do Vite (que só existe em `npm run dev`). Em produção (build estático servido pela Vercel), isso resultava em chamadas para o próprio domínio da Vercel, sem backend nenhum ali.

**Correção:** introduzida variável de ambiente `VITE_API_URL`, com fallback para o proxy em dev:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1'
```
Aplicado tanto na criação da instância `axios` quanto na chamada de refresh token (que usava `axios.post` direto com caminho relativo — bug irmão do mesmo problema, também corrigido).

### 4. Bug: `alembic upgrade head` (Pre-Deploy Command) falhou silenciosamente no primeiro deploy

Resultado: banco do Render ficou **sem nenhuma tabela**, causando `500 Internal Server Error` (`UndefinedTableError: relation "users" does not exist`) em qualquer tentativa de login.

**Correção manual (contorno imediato):** migrations rodadas do computador local, apontando para a **External Database URL** do Render:
```bash
$env:DATABASE_URL="postgresql+asyncpg://usuario:senha@host.oregon-postgres.render.com/db?ssl=require"
alembic upgrade head
```
Duas descobertas no caminho:
- **`?ssl=require` é obrigatório** na URL para `asyncpg` ao conectar externamente no Postgres do Render (sem isso: `InvalidAuthorizationSpecificationError: SSL/TLS required`).
- Usar a **External** URL (com domínio completo `.oregon-postgres.render.com`) é necessário para conexões de fora da rede do Render; a **Internal** URL (usada pelo próprio Web Service em produção) não é alcançável do computador local.

**Causa raiz do Pre-Deploy Command não pendente de investigação mais profunda** — ficou resolvido operacionalmente rodando a migration manualmente uma vez; deploys futuros devem ser monitorados para confirmar se o Pre-Deploy Command passa a funcionar corretamente.

### 5. Bug funcional: status `assigned` obsoleto no frontend causando erro 422 em produção

Ao tentar mudar o status de uma OS para "Atribuída" em produção, a API retornava `422` com `type: "enum"` — o backend só aceita `draft`, `scheduled`, `in_progress`, `completed`, `invoiced`, `cancelled`. O valor `assigned` era resquício de uma versão anterior do modelo de dados (provavelmente da época da renomeação `assigned_to` → `technician_id`, Fase 2B) e ficou esquecido em **4 arquivos do frontend**: `api/orders.ts` (union type), `DashboardPage.tsx`, `OrderDetailPage.tsx` (incluindo a tabela `VALID_TRANSITIONS` da FSM local, que replicava incorretamente a FSM do backend) e `OrdersPage.tsx`.

**Correção:** removidas todas as ocorrências de `assigned` como status; `VALID_TRANSITIONS` do frontend corrigida para bater com o enum real do backend:
```typescript
const VALID_TRANSITIONS: Record<string, ServiceOrderDetail['status'][]> = {
    draft: ['scheduled', 'cancelled'],
    scheduled: ['in_progress', 'cancelled'],
    in_progress: ['completed', 'cancelled'],
    completed: ['invoiced'],
    invoiced: [],
    cancelled: [],
}
```

### 6. Feature nova: adicionar itens (peças/serviços) à Ordem de Serviço

Endpoint `POST /api/v1/orders/{order_id}/items` já existia no backend desde fases anteriores, mas **nunca tinha sido implementado no frontend** — só existia leitura (`getItems`), não criação. Implementado nesta sessão:
- `addItem` adicionado em `src/api/orders.ts`.
- Modal de criação de item em `OrderDetailPage.tsx`, com `react-hook-form` + Zod, campos `item_type` (`labor`/`part`/`travel`/`other`), `description`, `quantity`, `unit_price`.
- **Bug de tipagem TypeScript encontrado e corrigido:** `z.coerce.number()` no schema Zod gera uma diferença entre o tipo de entrada do formulário (`string | number`, o que o `<input>` realmente entrega) e o tipo de saída (`number`, após coerção). `useForm<ItemFormData>` usando só um genérico causava erro `Type 'unknown' is not assignable to type 'number'`. **Correção:** uso dos três genéricos do `useForm` (`TFieldValues`, `TContext`, `TTransformedValues`), com `z.input<>` para entrada e `z.output<>` para saída:
```typescript
type ItemFormInput = z.input<typeof itemSchema>
type ItemFormData = z.output<typeof itemSchema>

useForm<ItemFormInput, unknown, ItemFormData>({ resolver: zodResolver(itemSchema), ... })
```

### 7. Dashboard: novo card "Agendadas" + gráfico mensal de OS

- Card `scheduled` (📅 "Agendadas") adicionado a `STAT_STATUSES` em `DashboardPage.tsx`, ocupando o espaço que antes seria do `assigned` removido — grid responsivo já dinâmico, sem necessidade de ajuste de layout.
- Gráfico de barras "Ordens de serviço por mês" (últimos 6 meses) adicionado com **`recharts`** (nova dependência).
  - **Bug de instalação:** `npm install recharts` não trouxe `react-is` (peer dependency) corretamente — possivelmente relacionado ao `.npmrc` com `legacy-peer-deps=true` já existente no projeto (criado originalmente por causa do `openapi-typescript`). Erro em runtime: `Failed to resolve import "react-is" from recharts.js`. **Corrigido** com `npm install react-is` explícito + limpeza do cache do Vite (`node_modules/.vite`).
  - **Bug de tipagem no `Tooltip formatter`:** anotação explícita `(value: number) =>` conflitava com o tipo genérico `ValueType | undefined` esperado pelo `recharts`. **Corrigido** removendo a anotação de tipo explícita, deixando o TypeScript inferir do contexto JSX.
  - Agregação mensal feita client-side a partir dos dados já carregados pela query existente (`page_size: 50`) — sem necessidade de endpoint novo no backend nesta fase. **Nota para o futuro:** se o volume de OS crescer significativamente, considerar endpoint de agregação dedicado no backend em vez de agregação no frontend.

### 8. Bug operacional: webhook GitHub → Vercel atrasado

Dois commits consecutivos (`76b116d`, `bcb5135`) não dispararam deploy automático imediato na Vercel — o painel de Deployments não os listava por alguns minutos, mesmo com o push confirmado no GitHub. **Resolvido sozinho** após aguardar / forçar um commit vazio adicional; ambos os deployments pendentes apareceram e processaram em sequência logo em seguida. **Não foi identificada causa definitiva** — pode ter sido apenas atraso momentâneo do webhook, não uma falha de configuração. Vale observar se o padrão se repete em deploys futuros.

### 9. Ambientes local vs. produção — bancos de dados independentes (não é bug)

Registrado para evitar confusão futura: dados criados testando em `localhost` (banco Postgres local via Docker) **não aparecem** em produção (banco do Render), e vice-versa — são bancos de dados completamente separados. Isso é o comportamento correto e esperado da separação dev/produção.

### 10. Checkpoint final — suíte pytest local

Rodada após correção de uma pista falsa: a primeira tentativa retornou **68 erros** (igual ao número total de testes), sintoma de problema de configuração/ambiente único afetando todos os testes igualmente — não 68 bugs distintos. Causa: `backend/.env` local provavelmente ainda apontando para o banco do **Render** (de quando a migration manual foi rodada apontando para lá), em vez do Postgres **local**. Após confirmar `DATABASE_URL`/`POSTGRES_HOST=localhost` no `.env` e subir o Postgres local via Docker:
```
68 passed, 3869 warnings in 72.47s
```
**Checkpoint final da Fase 3 fechado com sucesso.**

---

## Fase 3 — Checklist final

- [x] Gerar `types/api.ts` via `openapi-typescript`
- [x] `assigned_to` → `technician_id` em todas as camadas
- [x] Build de produção do frontend validado
- [x] Suíte pytest (68/68) validada — **local, checkpoint final pós-deploy**
- [x] `hooks/useAuth.ts` vazio removido
- [x] `order_number` como `INTEGER` — migration concluída
- [x] Bug do shadcn CLI corrigido
- [x] `.npmrc` com `legacy-peer-deps=true`
- [x] CORS de produção configurado e validado
- [x] Dockerfile de produção — multi-stage, non-root, validado
- [x] Migrations rodando em produção (aplicadas manualmente; Pre-Deploy Command a monitorar)
- [x] Responsividade mobile — corrigida e validada
- [x] **Backend em produção (Render)** — `serviceflow-backend-5ljk.onrender.com`, health check e Swagger validados
- [x] **PostgreSQL em produção (Render)** — schema migrado, `?ssl=require` documentado para acesso externo
- [x] **Frontend em produção (Vercel)** — `serviceflow-liard.vercel.app`, `VITE_API_URL` configurada
- [x] **CORS_ORIGINS de produção** — atualizado com domínio real da Vercel
- [x] **Fluxo completo validado em produção** — login, criar cliente, criar OS, adicionar itens, transições de status, dashboard
- [x] **Bug de status `assigned` obsoleto** — removido do frontend em 4 arquivos
- [x] **Feature de adicionar itens (peças/serviços) à OS** — implementada do zero no frontend
- [x] **Dashboard: card "Agendadas" + gráfico mensal** — implementado com `recharts`

## Decisões Pendentes / A Revisar (baixa prioridade, pós-deploy)
*(lista herdada + itens novos desta sessão)*
- Soft delete vs `is_active`, RefreshToken blacklist, Checklist/ChecklistItem futuro, `computed_field` para `DATABASE_URL`, refatorar `OrdersPage.tsx` para shadcn `<Table>`, buscar `console.log` residuais, testar UsersPage com técnico logado, simplificar login eliminando `/auth/me` extra, refatorar `get_order` manual, exibir `order_number` no header de `OrderDetailPage`, aliases de tipo em `src/api/orders.ts`.
- Service Worker fantasma em `localhost:5173` — ainda não resolvido (`Application → Service Workers → Unregister` + `Clear site data`); segue mascarando testes de CSS na aba normal do navegador.
- Migrar `LoginPage.tsx`, `Sidebar.tsx`, `AppLayout.tsx` de `style={{}}` inline para Tailwind puro.
- Esconder colunas menos críticas das tabelas em mobile via `hidden sm:table-cell`.
- **Novo:** code-splitting por rota — `npm run build` já emite aviso de chunk >500kB (bundle principal ~1MB/316kB gzip), agravado pela adição do `recharts`. Não bloqueia produção, mas vale revisitar se o app continuar crescendo.
- **Novo:** investigar causa raiz do Pre-Deploy Command (`alembic upgrade head`) não ter rodado com sucesso no primeiro deploy do Render — monitorar próximos deploys para confirmar se o problema persiste.
- **Novo:** monitorar prazo de 90 dias do PostgreSQL gratuito do Render — decidir upgrade ou migração antes do vencimento.
- **Novo:** avaliar migração para Hetzner (infraestrutura paga, sem cold start/expiração) quando o projeto estiver pronto para uso comercial real com clientes pagantes.
- **Novo (opcional):** agregação do gráfico mensal do Dashboard é feita client-side sobre até 50 ordens — endpoint de agregação dedicado no backend pode ser necessário se o volume de dados crescer.

---

## Próximo Passo Recomendado

**A Fase 3 está concluída.** O ServiceFlow está em produção, publicamente acessível, com fluxo funcional completo validado (autenticação, clientes, ordens de serviço, itens, status, dashboard). Sugestões de próximos passos, em ordem de prioridade:

1. **Criar dados reais** (clientes e ordens de serviço de verdade, não mais testes) diretamente em produção, já que os testes ficaram no banco local.
2. **Convite a um segundo usuário de teste** (ex.: técnico real de uma das oficinas parceiras) para validar a experiência fora do olhar do desenvolvedor.
3. Revisar a lista de "Decisões Pendentes" acima e priorizar o que for relevante antes de abrir para clientes pagantes — com destaque para o prazo de expiração do banco gratuito do Render (90 dias) e a decisão de manter o free tier ou migrar para Hetzner.