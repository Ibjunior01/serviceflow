# ServiceFlow — Project Continuity Document

## Sessão Atual
**Fase:** 3 — Preparação para Deploy (Backend + Frontend)
**Status:** Ambiente de produção simulado localmente (Docker Compose + Caddy + Cloudflare Tunnel) **validado de ponta a ponta**, incluindo teste funcional completo em celular real (login, criar cliente, criar OS). Falta apenas: corrigir responsividade mobile, configurar variáveis de ambiente reais do Hetzner/Vercel, e rodar o checkpoint final de pytest antes do primeiro deploy pago.

## Progresso das Fases

| Fase | Descrição | Status |
|------|-----------|--------|
| 1A–1G | Backend completo (estrutura, models, schemas, auth, CRUD, endpoints, testes) | ✅ Concluída |
| 2A | Frontend React + Vite + Tailwind — todas as telas | ✅ Concluída |
| 2B | Polimento de UX + Preparação para Deploy | ✅ Concluída |
| 3 | Deploy — Backend (Hetzner) + Frontend (Vercel) | ⏳ Em andamento — infraestrutura local 100% validada |

## Decisões de Arquitetura (backend) — inalteradas desde sessões anteriores
- Async engine (asyncpg), API versionada em `/api/v1`, Settings via pydantic-settings com validação no boot
- UUID v4 como PK, `lazy="selectin"` obrigatório em relationships async, `ondelete` explícito em FKs
- Repository Pattern (`CRUDBase` genérico) + Service Layer, singletons de módulo
- `technician_id` (não `assigned_to`) em todas as camadas; `order_number` é `INTEGER` puro no banco, formatação `OS-0001` só no frontend
- Login via JSON `{"email", "password"}`; refresh sem blacklist no MVP
- Ver sessões anteriores para o histórico completo de bugs de nomenclatura (`assigned_to`→`technician_id`, `name`→`full_name`, `order_number` VARCHAR→INTEGER) — todos corrigidos e validados com 68/68 testes passando.

---

## Sessão Fase 3.5 — Deploy local completo + validação mobile (11/07/2026)

Sessão longa e trabalhosa, mas terminou com o ambiente de produção simulado 100% funcional, incluindo teste real em celular. Documentando os bugs encontrados em detalhe porque vários têm causas raiz não óbvias — vale a leitura antes de mexer em Caddy/Docker/Vite de novo.

### 1. CORS em produção — bug `NoDecode`

**Sintoma:** `pydantic_settings.exceptions.SettingsError` / `JSONDecodeError` ao subir o backend com `CORS_ORIGINS` definido como string separada por vírgula no `.env`.

**Causa:** o pydantic-settings tenta fazer `json.loads()` automaticamente em qualquer campo `list[...]` lido do `.env`, antes mesmo do `field_validator` rodar. Uma string tipo `"http://a.com,http://b.com"` não é JSON válido.

**Correção aplicada em `app/core/config.py`:**
```python
from typing import Annotated
from pydantic_settings import BaseSettings, NoDecode
from pydantic import field_validator

class Settings(BaseSettings):
    ...
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
```

`Annotated[list[str], NoDecode]` desliga o parsing automático de JSON só nesse campo, deixando o `field_validator` fazer o `.split(",")` normalmente.

**`main.py`** — middleware adicionado logo após `app = FastAPI(...)`, antes dos exception handlers e do `include_router`:
```python
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
`allow_credentials=True` é obrigatório (JWT via header `Authorization`), o que implica que `CORS_ORIGINS` nunca pode conter `"*"` — sempre domínios explícitos.

**Bug secundário corrigido:** `config.py` tinha `SECRET_KEY: str` declarado duas vezes (linhas duplicadas) — inofensivo (Python só usa a última), mas removido por limpeza.

### 2. `Dockerfile.prod` — multi-stage build

Criado `backend/Dockerfile.prod` (mantendo o `Dockerfile` de dev intacto, separado):
- **Stage `builder`**: `python:3.14-slim` + `gcc`/`libpq-dev` (compilação de `asyncpg`/`bcrypt`) → `pip install --user -r requirements.lock`
- **Stage `runtime`**: só `libpq5` (lib de runtime, sem headers de compilação) + usuário non-root (`appuser`) + `COPY --from=builder /root/.local /home/appuser/.local`
- `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`, sem `--reload`
- `.dockerignore` criado (`.venv/`, `__pycache__/`, `.env`, `tests/`, `.git/`, etc.)

**Bug encontrado:** build falhava com `ModuleNotFoundError: No module named 'email_validator'` — `requirements.lock` estava desatualizado em relação ao `requirements.txt` (dependência transitiva do `EmailStr` do Pydantic nunca foi propagada pro lock). **Corrigido** com `pip freeze > requirements.lock` no ambiente local, seguido de `docker build --no-cache` (build cacheado não pegava o lock novo automaticamente na primeira tentativa).

**Validado:** container sobe standalone, `/health` responde 200 com `{"status":"ok"}`.

### 3. `docker-compose.prod.yml` + `Caddyfile` — a parte mais difícil da sessão

**Estrutura final do compose** (raiz do projeto): serviços `postgres` (16-alpine, healthcheck via `pg_isready -U ... -d ...` — precisa do `-d <database>`, senão gera erro `FATAL: database "user" does not exist` em loop, porque o Postgres tenta abrir um banco com o mesmo nome do usuário por padrão), `backend` (usa `Dockerfile.prod`, `DATABASE_URL` sobrescrito via `environment:` apontando para `postgres:5432` — dentro da rede Docker, serviços se enxergam pelo nome, nunca por `localhost`), `caddy` (portas 80/443 publicadas, único serviço realmente exposto ao host Windows).

**Pegadinha de variáveis:** `${POSTGRES_USER}` etc. usados diretamente no YAML do compose (fora de `env_file:`) exigem um `.env` **na raiz do projeto** (onde o `docker compose` é executado) — different mechanism do `env_file:` dos serviços, que injeta variáveis *dentro* do container. Os dois são necessários e não se substituem.

**Caddyfile — histórico de bugs, do mais simples ao mais sutil:**
1. Typo `:433` em vez de `:443` — TLS falhava silenciosamente porque a porta configurada não é a publicada no compose.
2. Bloco `localhost { }` só responde a requisições com `Host: localhost` — ao testar via túnel (`Host: algo.trycloudflare.com`), o Caddy não casava a config e retornava 200 vazio (`Content-Length: 0`). Trocado temporariamente para `:443 { }` (coringa).
3. Com `:443 { }` sem hostname declarado, `tls internal` **nunca emite o certificado de folha** (só a CA raiz) — handshake TLS quebra com `tls: internal error` tanto local quanto via túnel. Diagnosticado inspecionando `/data/caddy/certificates` (inexistente) dentro do container.
4. **Causa raiz de fundo, corrigida:** em vez de brigar com certificado dinâmico para hostname coringa, a perna "túnel → Caddy local" foi movida para **HTTP puro (porta 80)** — a criptografia real (túnel → celular) já é garantida pela própria Cloudflare na borda; a perna interna nunca sai da máquina/rede Docker. Isso elimina a necessidade de TLS válido internamente.
5. Com bloco `:80 { }` adicionado, o Caddy aplicava **redirect automático HTTP→HTTPS** mesmo assim (`308 Permanent Redirect`), porque `auto_https` é ligado globalmente por padrão sempre que existe qualquer bloco HTTPS na config (o `localhost { tls internal }` mantido para testes locais). **Correção final:**
```
{
    auto_https off
}

localhost {
    tls internal
    reverse_proxy /api/* backend:8000
    reverse_proxy /health backend:8000
}

:80 {
    reverse_proxy /api/* backend:8000
    reverse_proxy /health backend:8000
}
```
`auto_https off` desliga tanto a emissão automática de certificado quanto os redirects — cada bloco de site passa a se comportar exatamente como declarado.

**Falsas pistas investigadas e descartadas durante o diagnóstico** (documentando para não repetir): conflito de porta com `wslrelay` (processo legítimo do Docker Desktop/WSL2, não era a causa), dessincronia de relógio Windows↔WSL2 (relógios estavam corretos, erro de cálculo de fuso horário meu), múltiplos processos `cloudflared` concorrentes (só havia um). O log `Failed to initialize DNS local resolver` do `cloudflared` é **cosmético** e aparece sempre, mesmo em túneis saudáveis — não indica problema.

**Comando de teste local que expôs cada bug:** `curl.exe -kv https://localhost/health` (headers completos) foi essencial para diferenciar "conexão recusada" de "TLS handshake falhou" de "200 vazio por Host mismatch".

### 4. Migrations em produção — validadas do zero

Com `docker compose down -v` (reset completo de volumes, incluindo `postgres_data`), confirmado banco genuinamente vazio (`\dt` → "Did not find any relations"). Rodado:
```powershell
docker compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```
As 3 revisions aplicaram em sequência sem erro; `\dt` depois confirmou as 7 tabelas esperadas (incluindo `alembic_version`). **Fluxo completo validado**: banco vazio → migrations → registro de usuário (`POST /auth/register`, 201) → login (`POST /auth/login`, 200) — tudo dentro do ambiente containerizado, via porta 80 do Caddy.

### 5. Cloudflare Tunnel — setup e pegadinhas

- `winget install --id Cloudflare.cloudflared` instala mas não atualiza o PATH da sessão atual do PowerShell — precisa reabrir o terminal, ou (nesse caso) usar o caminho completo: `C:\Program Files (x86)\cloudflared\cloudflared.exe`.
- Comando usado (perna backend): `& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://localhost:80` (HTTP puro, ver seção Caddyfile acima).
- URLs de "quick tunnel" são **efêmeras** — só existem enquanto aquele processo `cloudflared` específico está rodando; fechar o terminal mata a URL.
- **`Error 1033` / `Error 502`**: sempre investigar primeiro se o processo `cloudflared` ainda está vivo e se os containers (`docker compose ps`) ainda estão `Up` — várias vezes o Caddy tinha caído silenciosamente depois de comandos `up --build <service>` parciais sem `-d`.

### 6. Frontend — proxy do Vite + `allowedHosts`

`client.ts` usa `baseURL: '/api/v1'` (relativo) — depende do proxy do Vite (`vite.config.ts`) para rotear até o backend. Como o backend **não publica porta pro host** nesse setup (só o Caddy publica 80/443), o proxy precisa apontar para o Caddy, não direto pro backend:
```typescript
server: {
    proxy: {
        '/api': { target: 'http://127.0.0.1:80', changeOrigin: true },
    },
    allowedHosts: ['.trycloudflare.com'],
}
```
`allowedHosts` é necessário porque o Vite 5+ bloqueia por padrão requisições com `Host` header de domínios externos não listados (proteção de segurança nova) — sem isso, erro `Blocked request. This host ... is not allowed`. O coringa `.trycloudflare.com` evita precisar editar a cada novo túnel gerado (nome aleatório muda sempre).

**Importante:** como o proxy roda no processo Node do Vite (server-side), não há CORS envolvido nesse caminho — a chamada nunca é cross-origin do ponto de vista do navegador. `CORS_ORIGINS` do backend não precisou ser tocado para o teste mobile funcionar.

Segundo túnel, dedicado ao frontend: `cloudflared tunnel --url http://localhost:5173` (depois de rodar `npm run dev -- --host` para o Vite escutar em todas as interfaces).

### 7. Bug de ambiente duplicado — duas bases de dados diferentes

**Sintoma muito confuso:** login funcionava perfeitamente via `POST /api/v1/auth/login` batendo em `127.0.0.1:8000/docs`, mas o mesmo usuário/senha dava "e-mail ou senha inválidos" no frontend (via túnel).

**Causa raiz:** existiam **dois Postgres diferentes** em jogo:
1. Um container antigo (`backend-db-1`, de projeto/sessão anterior, publicando `5432` pro Windows) — alcançável via `localhost:5432`, usado por qualquer processo backend rodando **fora** do Docker (ex.: um `uvicorn --reload` solto).
2. O Postgres **do `docker-compose.prod.yml`** — sem porta publicada, acessível só de dentro da rede Docker via `postgres:5432` — é o que o backend containerizado (e, por consequência, o frontend via Caddy/túnel) realmente usa.

Testar em `127.0.0.1:8000/docs` sempre bateu no banco errado (antigo/dev), gerando a falsa sensação de que "funciona ali mas não no app". **Lição:** ao testar múltiplos ambientes (dev solto vs. Docker Compose) na mesma máquina, sempre confirmar explicitamente qual porta/processo está respondendo antes de comparar resultados.

**Resolução:** usuário `mobile@service.com` / `Senha123` registrado **direto no ambiente containerizado** via `Invoke-RestMethod` contra `http://localhost/api/v1/auth/register` (porta 80, através do Caddy) — esse sim compartilhado com o frontend.

### 8. Teste mobile completo — validado com sucesso ✅

No celular (Safari, via túnel do frontend), fluxo completo testado e confirmado:
1. Login com `mobile@service.com` — sucesso.
2. Criação de cliente ("Celteste") — sucesso.
3. Criação de OS ("Teste cel", vinculada ao cliente criado) — sucesso (havia dado erro `customer_id: Field required` na primeira tentativa, por tentar criar OS antes de existir qualquer cliente cadastrado — resolvido cadastrando o cliente primeiro).

Confirmado também via desktop (`http://localhost:5173`), mesma base de dados compartilhada: Dashboard mostrando a OS criada pelo celular, listagem de Ordens (`OS-0001`, formatação correta), listagem de Clientes, listagem de Usuários — tudo consistente.

### 9. Pendência conhecida, não resolvida ainda

**Responsividade mobile:** a tela de login (e possivelmente outras) aparece cortada no celular, exigindo scroll horizontal / zoom manual. Ainda não diagnosticada a fundo — hipóteses não testadas: meta tag de viewport ausente no `index.html`, ou largura fixa em algum container de `LoginPage.tsx`. **Não bloqueou a validação funcional** (login e CRUD funcionaram apesar do layout ruim), mas precisa ser corrigida antes de considerar o app pronto para uso real em campo.

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
- [ ] **Corrigir responsividade mobile** (viewport/CSS) — pendência ativa, não iniciada
- [ ] Variáveis de ambiente de produção reais — Hetzner (`DATABASE_URL`, `SECRET_KEY` forte gerado via `openssl rand -hex 32` — o atual no `.env` é um placeholder curto, **não pode ir para produção**) e Vercel (URL pública da API)
- [ ] Rodar pytest uma última vez como checkpoint final antes do primeiro deploy pago no Hetzner

## Decisões Pendentes / A Revisar (baixa prioridade, pós-deploy)
*(lista herdada de sessões anteriores, sem mudanças — ver seção completa no histórico)*
- Soft delete vs `is_active`, RefreshToken blacklist, Checklist/ChecklistItem futuro, `computed_field` para `DATABASE_URL`, refatorar `OrdersPage.tsx` para shadcn `<Table>`, buscar `console.log` residuais, testar UsersPage com técnico logado, code-splitting por rota, simplificar login eliminando `/auth/me` extra, refatorar `get_order` manual, exibir `order_number` no header de `OrderDetailPage`, aliases de tipo em `src/api/orders.ts`.

---

## Próximo Passo Recomendado

**Corrigir a responsividade mobile antes de avançar para Hetzner/Vercel.**

Motivo: a infraestrutura (Docker, Caddy, túnel, banco, CORS) está agora comprovadamente sólida — todo o trabalho pesado e imprevisível dessa sessão foi justamente ali. Responsividade é um problema **isolado e de escopo pequeno** (provavelmente uma meta tag ou um container com largura fixa), rápido de corrigir e validar com o mesmo setup de túnel que já está funcionando. Resolver isso agora, enquanto o ambiente de teste mobile está "quente" e validado, evita ter que remontar toda a infraestrutura de teste (Docker + 2 túneis) de novo mais tarde só para essa validação visual.

Só depois disso faz sentido seguir para: gerar `SECRET_KEY` forte, configurar variáveis de ambiente reais do Hetzner/Vercel, e rodar o checkpoint final de pytest antes do primeiro deploy pago.