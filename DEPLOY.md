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
- No projeto da Vercel → aba **Deployments** → o deploy mais recente fica **Ready**.
- Clique em **Visit** para abrir (ex.: `https://storyrus.vercel.app`). Essa é a home (landing).
- A cada `git push` no `main`, a Vercel atualiza a produção automaticamente.

---

## 3) Domínio da GoDaddy no Vercel

A **GoDaddy só guarda o domínio**. O site continua hospedado na Vercel (`storyrus.vercel.app`). Não use hospedagem, construtor de sites nem encaminhamento da GoDaddy.

### Na Vercel

1. Abra o projeto **storyrus** → **Settings → Domains**.
2. Adicione o domínio raiz (ex.: `seudominio.com`) e o `www` (ex.: `www.seudominio.com`).
3. Escolha o redirecionamento **www → raiz** (ou o contrário). A Vercel emite o HTTPS sozinha.
4. Abra o card do domínio e **copie os registros que a Vercel mostrar**. O CNAME do `www` pode ser específico do projeto (não invente o valor).

### Na GoDaddy (DNS)

Painel GoDaddy → **Domínios** → o domínio → **DNS** / **Gerenciar DNS**.

**Não apague MX** se o e-mail do domínio estiver na GoDaddy (ou em outro provedor). Apague só o que aponta o *site* para a GoDaddy.

| Tipo  | Nome | Valor | TTL |
|-------|------|-------|-----|
| **A** | `@` | `76.76.21.21` | 600 (ou 1 hora) |
| **CNAME** | `www` | o valor do card da Vercel (em geral `cname.vercel-dns.com`) | 600 |

Antes de salvar, remova conflitos:

- Registro **A** antigo em `@` (parking da GoDaddy: IPs tipo `3.33.…`, `15.197.…`, `Parked`).
- **CNAME** de `www` apontando para parking / `secureserver` / construtor de sites.
- **Encaminhamento de domínio** (Domain Forwarding) — desligue.
- **Hospedagem / Website Builder** da GoDaddy no mesmo domínio — desconecte.

Mantenha os **nameservers da GoDaddy**. Só mude nameserver para `ns1.vercel-dns.com` / `ns2.vercel-dns.com` se quiser a Vercel gerenciando *todo* o DNS (aí os MX de e-mail precisam ser recriados na Vercel).

### Conferir

1. Na Vercel, o domínio deve ir para **Valid Configuration**.
2. Abra `https://seudominio.com` e `https://www.seudominio.com` — landing e `/app` (estúdio) devem responder.
3. O front chama `/v1` no **mesmo domínio**; a Vercel faz proxy para o Render. Não precisa CORS extra.

Propagação: minutos na maioria dos casos; até 24–48 h se a GoDaddy tinha parking/encaminhamento. Se ficar inválido, o card da Vercel mostra o registro que ainda falta.

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
| Domínio   | GoDaddy → Vercel | DNS na GoDaddy; site na Vercel (não hospeda na GoDaddy) |
| API       | Render     | Docker; `dockerCommand` roda `alembic upgrade` + uvicorn |
| Worker    | Render     | Processa os jobs de IA |
| Banco     | Render Postgres | `DATABASE_URL` automática |
| Storage   | Cloudflare R2 | Variáveis `STORAGE_*` |
| Redis     | — (opcional) | Sem ele, worker faz polling do banco |
