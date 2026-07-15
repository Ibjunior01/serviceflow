# ServiceFlow — Project Continuity Document

## Sessão Atual
**Fase:** 3 — Preparação para Deploy (Backend + Frontend)
**Status:** Ambiente de produção simulado localmente (Docker Compose + Caddy + Cloudflare Tunnel) **validado de ponta a ponta**, incluindo teste funcional completo em celular real (login, criar cliente, criar OS). **Responsividade mobile corrigida e validada** em todas as telas principais. Falta apenas: configurar variáveis de ambiente reais do Hetzner/Vercel e rodar o checkpoint final de pytest antes do primeiro deploy pago.

## Progresso das Fases

| Fase | Descrição | Status |
|------|-----------|--------|
| 1A–1G | Backend completo (estrutura, models, schemas, auth, CRUD, endpoints, testes) | ✅ Concluída |
| 2A | Frontend React + Vite + Tailwind — todas as telas | ✅ Concluída |
| 2B | Polimento de UX + Preparação para Deploy | ✅ Concluída |
| 3 | Deploy — Backend (Hetzner) + Frontend (Vercel) | ⏳ Em andamento — infraestrutura local e responsividade 100% validadas |

## Decisões de Arquitetura (backend) — inalteradas desde sessões anteriores
- Async engine (asyncpg), API versionada em `/api/v1`, Settings via pydantic-settings com validação no boot
- UUID v4 como PK, `lazy="selectin"` obrigatório em relationships async, `ondelete` explícito em FKs
- Repository Pattern (`CRUDBase` genérico) + Service Layer, singletons de módulo
- `technician_id` (não `assigned_to`) em todas as camadas; `order_number` é `INTEGER` puro no banco, formatação `OS-0001` só no frontend
- Login via JSON `{"email", "password"}`; refresh sem blacklist no MVP
- Ver sessões anteriores para o histórico completo de bugs de nomenclatura (`assigned_to`→`technician_id`, `name`→`full_name`, `order_number` VARCHAR→INTEGER) — todos corrigidos e validados com 68/68 testes passando.

---

## Sessão Fase 3.6 — Correção de responsividade mobile (12–14/07/2026)

Pendência aberta na sessão anterior (3.5), agora fechada. Padrão raiz identificado no início: o frontend usa `style={{}}` inline em quase todo componente, e inline style sempre vence classe CSS — então qualquer largura/grid fixo em `style` nunca respondia a media query nenhuma, mesmo quando o Tailwind estava configurado corretamente.

### 1. Diagnóstico inicial — viewport e Tailwind descartados como causa

- `index.html` já tinha `<meta name="viewport" content="width=device-width, initial-scale=1.0">` correto desde o início.
- Tailwind v4 confirmado configurado corretamente: plugin `@tailwindcss/vite` no `vite.config.ts`, `@import "tailwindcss"` no `src/index.css`. Não havia (nem precisa haver, no v4) `tailwind.config.js`.
- **Armadilha encontrada:** um Service Worker fantasma ficou registrado em `localhost:5173` (origem não identificada com certeza — possivelmente sobra de outro projeto Vite testado na mesma porta) servindo uma versão em cache do app. Isso mascarou todas as correções de CSS por várias rodadas de teste — mudanças no código não apareciam na aba normal do Chrome, só em aba anônima. **Sintoma característico:** funciona em aba anônima, não funciona em aba normal, mesmo com "Disable cache" do DevTools marcado (esse não desliga Service Worker). **Correção pendente, não crítica:** `DevTools → Application → Service Workers → Unregister` + `Clear site data`. Enquanto não resolvido, **sempre validar mudanças de CSS/layout em aba anônima**.

### 2. `LoginPage.tsx` — painel de branding fixo em 420px

Painel esquerdo (dark, marketing) usava `flex: '0 0 420px'` inline sem media query — sozinho já estourava a largura de qualquer celular. **Correção:** painel movido para `className="hidden md:flex md:flex-none md:w-[420px] ..."` (Tailwind), escondendo completamente abaixo de 768px — padrão comum em SaaS mobile (Linear, Stripe, etc.), foco total no formulário em telas pequenas. Padding do painel direito também migrado de `style` fixo para `className="px-4 py-8 md:px-12 md:py-12"`.

### 3. `Sidebar.tsx` + `AppLayout.tsx` — menu lateral fixo, sem navegação mobile

Sidebar era `width: '220px'` fixo, sempre visível, sem nenhum jeito de esconder/mostrar. **Correção:** convertida para drawer deslizante — escondida por padrão em mobile (`-translate-x-full`), abre com overlay via `AppLayout` (novo estado `sidebarOpen` + botão hambúrguer numa barra superior nova, só visível em mobile). Fecha automaticamente ao clicar num link ou no overlay. Em desktop (`md:` +) permanece fixa, comportamento idêntico ao original.

**Bug secundário encontrado neste componente:** `h-screen` (`100vh`) cortava o rodapé do menu (botão de logout) no Safari iOS quando a barra de endereço está visível, porque `100vh` no Safari mobile é calculado com a barra retraída. **Corrigido** trocando para `h-dvh` (dynamic viewport height, suportado nativamente pelo Tailwind v4), que se ajusta automaticamente à barra do navegador aparecendo/sumindo.

### 4. Padrão recorrente encontrado e corrigido em 4 páginas: grids fixos de 2/4 colunas + tabelas sem scroll contido

Auditoria sistemática via `Select-String "gridTemplateColumns|width: '\d|flex: '0"` em todo `src/` encontrou o mesmo padrão repetido:

- **`DashboardPage.tsx`**: grid de stat cards `repeat(4, 1fr)` fixo → `className="grid grid-cols-2 sm:grid-cols-4 gap-4"`. Tabela "Ordens recentes" sem wrapper de scroll → envolvida em `<div style={{ overflowX: 'auto' }}>`.
- **`OrderDetailPage.tsx`**: grid de cards (Cliente/Técnico/Datas/Total) `1fr 1fr` fixo → `grid-cols-1 sm:grid-cols-2`. Tabela de itens da ordem → mesmo tratamento de `overflowX: auto`. Header (título + botão "Alterar status") ganhou `flexWrap: 'wrap'` para não espremer em telas estreitas.
- **`OrdersPage.tsx`**: grid do modal de criação (Prioridade + Agendamento) `1fr 1fr` fixo → `grid-cols-1 sm:grid-cols-2`. As duas tabelas (skeleton de loading e dados reais) → `overflowX: auto`. Modal ganhou `maxHeight: calc(100vh - 32px)` + `overflowY: auto` (evita corte em celulares pequenos com muitos campos). Header da página e paginação ganharam `flexWrap: 'wrap'`.

**Padrão de correção consistente em todos os casos:** grids de N colunas fixas viram Tailwind responsivo (`grid-cols-1 sm:grid-cols-2` ou `grid-cols-2 sm:grid-cols-4`, conforme o caso); tabelas ganham wrapper `overflow-x-auto` — deixando a tabela rolar **dentro** do próprio card, sem nunca empurrar a largura da página inteira (era a causa do "preciso passar a tela pra ver o último indicador" relatado no teste mobile).

### 5. Validação final

Testado em celular real (Safari, via túnel do frontend) e em DevTools (aba anônima): Dashboard, Ordens de Serviço (lista + modal + detalhe), Configurações, menu lateral — todos renderizando em coluna única, sem corte nem scroll horizontal indesejado, botão de logout visível, hambúrguer funcional. **Responsividade mobile considerada fechada.**

---

## Fase 3 — Checklist atualizado

- [x] Gerar `types/api.ts` via `openapi-typescript`
- [x] `assigned_to` → `technician_id` em todas as camadas
- [x] Build de produção do frontend validado
- [x] Suíte pytest (68/68) validada
- [x] `hooks/useAuth.ts` vazio removido
- [x] `order_number` como `INTEGER` — migration concluída
- [x] Bug do shadcn CLI corrigido
- [x] `.npmrc` com `legacy-peer-deps=true`
- [x] **CORS de produção configurado e validado** (bug `NoDecode` resolvido)
- [x] **Dockerfile de produção** — multi-stage, non-root, validado (bug `email-validator` no lock resolvido)
- [x] **`docker-compose.prod.yml` + Caddyfile** — validado (múltiplos bugs de TLS/`auto_https` resolvidos)
- [x] **Migrations rodando em produção** — validadas do zero (banco vazio → schema completo)
- [x] **Teste mobile via Cloudflare Tunnel** — validado, incluindo fluxo funcional completo (login, criar cliente, criar OS)
- [x] **Responsividade mobile** — corrigida e validada em LoginPage, Sidebar/AppLayout, DashboardPage, OrderDetailPage, OrdersPage
- [ ] Variáveis de ambiente de produção reais — Hetzner (`DATABASE_URL`, `SECRET_KEY` forte gerado via `openssl rand -hex 32` — o atual no `.env` é um placeholder curto, **não pode ir para produção**) e Vercel (URL pública da API)
- [ ] Rodar pytest uma última vez como checkpoint final antes do primeiro deploy pago no Hetzner

## Decisões Pendentes / A Revisar (baixa prioridade, pós-deploy)
*(lista herdada de sessões anteriores + 1 item novo desta sessão)*
- Soft delete vs `is_active`, RefreshToken blacklist, Checklist/ChecklistItem futuro, `computed_field` para `DATABASE_URL`, refatorar `OrdersPage.tsx` para shadcn `<Table>`, buscar `console.log` residuais, testar UsersPage com técnico logado, code-splitting por rota, simplificar login eliminando `/auth/me` extra, refatorar `get_order` manual, exibir `order_number` no header de `OrderDetailPage`, aliases de tipo em `src/api/orders.ts`.
- **Novo:** investigar e remover o Service Worker fantasma registrado em `localhost:5173` (`Application → Service Workers → Unregister` + `Clear site data`) — não bloqueia nada, mas continua mascarando testes futuros de CSS/layout na aba normal do navegador até ser removido.
- **Novo (opcional):** migrar `LoginPage.tsx`, `Sidebar.tsx` e `AppLayout.tsx` de `style={{}}` inline para Tailwind puro, por consistência com o resto do codebase (que já usa shadcn/Tailwind) — não é urgente, mas evita o mesmo tipo de bug de especificidade CSS reaparecer em telas futuras.
- **Novo (opcional):** considerar esconder colunas menos críticas das tabelas (ex.: "Data") em mobile via `hidden sm:table-cell`, reduzindo a necessidade de scroll horizontal — decisão de produto, não implementado nesta sessão.

---

## Próximo Passo Recomendado

**Configurar variáveis de ambiente reais de produção (Hetzner + Vercel) e rodar o checkpoint final de pytest.**

Motivo: com a infraestrutura local (Docker, Caddy, túnel, banco, CORS) e a responsividade mobile agora comprovadamente sólidas, os únicos itens restantes antes do primeiro deploy pago são de configuração, não de código:

1. Gerar `SECRET_KEY` forte: `openssl rand -hex 32` (o valor atual no `.env` é um placeholder curto e **não pode** ir para produção).
2. Definir variáveis de ambiente reais no Hetzner: `DATABASE_URL` (apontando para o Postgres de produção), `SECRET_KEY` (gerada no passo 1), `CORS_ORIGINS` (domínio real do Vercel, não `localhost`).
3. Definir variável de ambiente no Vercel: URL pública da API no Hetzner (substituindo o proxy local do Vite, que só existe em dev).
4. Rodar a suíte pytest (68/68) uma última vez como checkpoint final, antes de comprometer a infraestrutura paga.

Só depois desses 4 passos faz sentido seguir para o primeiro deploy real no Hetzner (backend) e Vercel (frontend).