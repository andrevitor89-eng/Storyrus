# Deploy — Story R Us

Guia para colocar o projeto no ar: **frontend na Vercel** e **backend no Render**.

## Arquitetura

```
Navegador
   │
   ▼
Vercel (frontend Vite/React)  ──/v1/* (proxy)──►  Render (API FastAPI)
                                                      │
                                          ┌───────────┼───────────┐
                                          ▼           ▼           ▼
                                     Postgres     Worker      Cloudflare R2
                                     (Render)   (jobs IA)      (storage)
```

- **Frontend**: `apps/web` (Vite + React). Vai na **Vercel**.
- **Backend**: `backend` (FastAPI). Vai no **Render** (Docker), com um **worker** que processa os jobs (personagem, história, e-book, vídeo) e um **Postgres**.
- **Storage**: **Cloudflare R2** (em produção; o MinIO é só para desenvolvimento local).
- **Redis**: opcional. Sem ele, o worker faz *polling* do banco e tudo funciona.

> As chaves (Gemini, Anthropic, Kling, ElevenLabs, R2) **nunca** ficam no repositório — só em variáveis de ambiente. O `.env` está no `.gitignore`.
>
> O worker precisa de **ffmpeg** no PATH para o vídeo narrado (já instalado na imagem Docker do backend). Sem ffmpeg, o fallback gera um GIF slideshow.

---

## 1) Backend no Render

1. Acesse **render.com** → **New → Blueprint** → conecte o repositório `Storyrus`.
2. O Render lê o `render.yaml` e cria 3 recursos: **storyrus-api** (web), **storyrus-worker** (worker) e **storyrus-db** (Postgres).
3. Em cada serviço (api e worker), preencha as variáveis marcadas como *secret* em **Environment**:
   - `GEMINI_API_KEY` — chave do Gemini no formato `AIza...`
   - `ANTHROPIC_API_KEY` — `sk-ant-...`
   - `KLING_ACCESS_KEY` / `KLING_SECRET_KEY` — (só se for usar vídeo)
   - `STORAGE_BUCKET` — ex.: `storyrus`
   - `STORAGE_ENDPOINT_URL` — `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`
   - `STORAGE_PUBLIC_ENDPOINT_URL` — **mesma URL acima** (no R2 é o mesmo endpoint)
   - `STORAGE_ACCESS_KEY` / `STORAGE_SECRET_KEY` — token S3 do R2
   - (`JWT_SECRET` e `WEBHOOK_SIGNING_SECRET` o Render gera sozinho.)
   - `DATABASE_URL` é injetada automaticamente pelo banco do Blueprint.
4. Aguarde o build. Quando a **storyrus-api** ficar *Live*, copie a URL (ex.: `https://storyrus-api.onrender.com`).

> Free tier do Render hiberna após inatividade e o Postgres free expira em ~90 dias — ok para testes.

### Cloudflare R2 (storage)
- Painel Cloudflare → **R2** → crie um bucket (ex.: `storyrus`).
- **Manage R2 API Tokens** → crie um token com permissão *Object Read & Write* → use o **Access Key ID** e **Secret Access Key**.
- Endpoint: `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` (use o ID da conta, não o nome do bucket).

---

## 2) Frontend na Vercel

1. Acesse **vercel.com** → **Add New → Project** → importe o repositório `Storyrus`.
2. **Root Directory**: deixe na **raiz** do repo (o `vercel.json` da raiz já manda construir `apps/web`).
3. Framework/Build/Output já vêm do `vercel.json`. Clique em **Deploy**.
4. Confirme que o `/v1` aponta para a sua API do Render:
   - Em `vercel.json` (raiz e `apps/web`), a `destination` deve ser a URL real da api (ex.: `https://storyrus-api.onrender.com`). Se a URL do Render for diferente, ajuste e dê `git push` (a Vercel redeploya sozinha).

### Como ver o site
- URL canônica: **https://storyrus.ai**
- `https://www.storyrus.ai` redireciona para a raiz.
- `https://storyrus.vercel.app` redireciona para `https://storyrus.ai` (regra nos `vercel.json`).
- A cada `git push` no `main`, a Vercel atualiza a produção automaticamente.

---

## 3) Domínio da GoDaddy no Vercel

A **GoDaddy só guarda o DNS**. O site continua hospedado na Vercel. Não use hospedagem, construtor de sites nem encaminhamento da GoDaddy.

O projeto **storyrus** já tem `storyrus.ai` e `www.storyrus.ai`. O `www` e o `storyrus.vercel.app` redirecionam para `https://storyrus.ai` via `vercel.json`.

Há e-mail Microsoft 365 no domínio (`storyrus-ai.mail.protection.outlook.com`). **Não apague MX** e **não troque nameservers**.

### Na Vercel

Já feito: Settings → Domains no projeto **storyrus**. HTTPS a Vercel emite sozinha depois do DNS.

### Na GoDaddy (DNS)

Painel GoDaddy → **Domínios** → `storyrus.ai` → **DNS** / **Gerenciar DNS**.

**Criar/atualizar** (TTL 600):

| Tipo  | Nome | Valor |
|-------|------|-------|
| **A** | `@` | `216.198.79.1` |
| **A** | `@` | `64.29.17.1` |
| **CNAME** | `www` | `b1f150d36b8308d7.vercel-dns-017.com` |

Fallback se a GoDaddy só aceitar um A: `@` → `76.76.21.21`. Alternativa de CNAME: `cname.vercel-dns.com`.

**Remover só o parking do site** (hoje em `3.33.130.190` e `15.197.148.33`):

- Registros **A** antigos em `@` com esses IPs.
- **CNAME** de `www` apontando para `storyrus.ai` / parking / `secureserver`.
- **Encaminhamento de domínio** (Domain Forwarding) — desligar.
- Website Builder / hospedagem GoDaddy nesse domínio — desconectar.

**Manter:**

- Nameservers `ns09.domaincontrol.com` / `ns10.domaincontrol.com`
- MX `storyrus-ai.mail.protection.outlook.com` (e TXT/CNAME de Outlook, se existirem)

### Conferir

1. Vercel: `storyrus.ai` e `www` em **Valid Configuration**.
2. `https://storyrus.ai` e `https://www.storyrus.ai` — landing e `/app`.
3. `https://storyrus.vercel.app` deve redirecionar para `https://storyrus.ai`.
4. O front chama `/v1` no **mesmo domínio**; a Vercel faz proxy para o Render. Não precisa CORS extra.

Propagação: minutos na maioria dos casos; até 24–48 h se havia parking. Reverificar com `vercel domains verify storyrus.ai`.

---

## 4) Ligar frontend ↔ backend

1. Backend no ar no Render → copie a URL da api.
2. Ajuste a `destination` nos `vercel.json` para essa URL (se ainda não estiver).
3. `git push` → a Vercel redeploya. Agora o estúdio (`/app`) chama o backend e gera de verdade.

---

## Desenvolvimento local (opcional)

Tudo roda em Docker:

```bash
docker compose up -d --build
```

- Web: http://localhost:5173
- API: http://localhost:8000/docs
- Storage local (MinIO): console em http://localhost:9001
- As variáveis ficam em `backend/.env` (veja `backend/.env.example`).

---

## Resumo rápido

| Camada    | Plataforma | Observação |
|-----------|------------|------------|
| Frontend  | Vercel     | Root = raiz; `vercel.json` constrói `apps/web` |
| Domínio   | GoDaddy → Vercel | `storyrus.ai`; DNS na GoDaddy; site na Vercel |
| API       | Render     | Docker; `dockerCommand` roda `alembic upgrade` + uvicorn |
| Worker    | Render     | Processa os jobs de IA |
| Banco     | Render Postgres | `DATABASE_URL` automática |
| Storage   | Cloudflare R2 | Variáveis `STORAGE_*` |
| Redis     | — (opcional) | Sem ele, worker faz polling do banco |
