# Plataforma de Histórias — FortesHub

Transforma uma foto em um personagem ilustrado, gera uma história, monta um ebook
e (opcional) um vídeo animado. Pipeline assíncrono de IA com créditos, jobs
idempotentes, moderação/segurança e provedores reais (Nano Banana Pro, Claude, Kling).

## Monorepo

```
backend/      # API (FastAPI) + workers + clients de IA   → backend/README.md
apps/web/     # Frontend (Vite + React + TS) + testes (Vitest/MSW) + E2E (Playwright)
apps/mobile/  # App Expo (React Native): mesmo fluxo no celular → apps/mobile/README.md
.github/      # CI: ruff+pytest (backend), tsc+vitest+build (web), Playwright (e2e)
```

## CI

`.github/workflows/ci.yml` roda em push/PR:

- **backend** — `ruff check` + `pytest`.
- **frontend** — `tsc --noEmit` + `vitest run` + `vite build`.
- **e2e** — `playwright test` (navegador real, API mockada), com relatório anexado.

## Rodar local

O compose em `backend/docker-compose.yml` sobe **Postgres + Redis + API + worker**
(não inclui frontend nem MinIO):

```bash
cp backend/.env.example backend/.env   # preencha as CHAVES depois
cd backend && docker compose up --build
#  API: http://localhost:8000/docs
```

Popular dados e validar o fluxo da API:

```bash
cd backend
docker compose run --rm api python scripts/seed.py
# cria demo@forteshub.com / demo12345 (50 créditos)
API_URL=http://localhost:8000 python scripts/demo_flow.py
# exercita signup → projeto → upload → etapas → jobs
```

Frontend em modo dev (com a API já de pé):

```bash
cd apps/web && npm install && npm run dev   # proxy /v1 -> :8000 (VITE_API_PROXY)
#  Web: http://localhost:5173
```

Deploy em produção: `DEPLOY.md` (Vercel + Render). Detalhes da API: `backend/README.md`.

## Chaves a preencher (`backend/.env`)

Tudo funciona offline para desenvolvimento, mas o pipeline real precisa de:

| Variável | Para quê |
|---|---|
| `GEMINI_API_KEY` | Nano Banana Pro (cenas / fallback sem Fal) |
| `FAL_KEY` | Fal.ai PuLID (avatar + passe de cabeça). Sem chave, cai no Gemini |
| `ANTHROPIC_API_KEY` | Claude (geração da história) |
| `KLING_ACCESS_KEY` / `KLING_SECRET_KEY` | Kling (vídeo) |
| `STORAGE_ACCESS_KEY` / `STORAGE_SECRET_KEY` / `STORAGE_BUCKET` / `STORAGE_ENDPOINT_URL` | R2/S3 (uploads e entregáveis) |
| `JWT_SECRET` / `WEBHOOK_SIGNING_SECRET` | segredos da aplicação |

Sem as chaves de IA/storage, a API e os workers sobem e o fluxo de
créditos/jobs/idempotência roda; as chamadas de geração falham de forma controlada
(estado `FAILED` + estorno).

Storage local: configure `STORAGE_*` apontando para **Cloudflare R2** (ou outro
S3-compatible). O compose **não** sobe MinIO — veja `DEPLOY.md`.

## Fluxo

1. Abre o estúdio (`/app`) — o front pede um **JWT de convidado** (`POST /v1/auth/guest`).
2. Cria projeto e escolhe o estilo.
3. Envia a foto (URL assinada).
4. Dispara as etapas (avatar → história → ebook → vídeo). Cada uma debita créditos,
   enfileira um job e responde **202**; o worker processa e o front acompanha o
   progresso ao vivo.

Signup/login (`POST /v1/auth/signup` / `login`) continuam disponíveis na API
(ex.: seed/demo e mobile); o web atual é guest-first.
