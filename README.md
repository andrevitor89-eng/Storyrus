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

## Subir tudo (um comando)

O `docker-compose.yml` na raiz sobe **db + redis + api + worker + web** juntos:

```bash
make init                     # copia backend/.env (preencha as CHAVES depois)
make up                       # docker compose up --build
#  API: http://localhost:8000/docs   ·   Web: http://localhost:5173
```

Popular dados e validar o fluxo ponta a ponta:

```bash
make seed                     # cria demo@forteshub.com / demo12345 (50 créditos)
make demo                     # exercita signup → projeto → upload → etapas → jobs
```

> Sem `make`, use os comandos equivalentes: `cp backend/.env.example backend/.env`,
> `docker compose up --build`, `docker compose run --rm api python scripts/seed.py`.

Rodar só o frontend em modo dev (com a API já de pé):

```bash
cd apps/web && npm install && npm run dev   # proxy /v1 -> :8000 (VITE_API_PROXY)
```

## Chaves a preencher (`backend/.env`)

Tudo funciona offline para desenvolvimento, mas o pipeline real precisa de:

| Variável | Para quê |
|---|---|
| `GEMINI_API_KEY` | Nano Banana Pro (personagem e ilustrações) |
| `ANTHROPIC_API_KEY` | Claude (geração da história) |
| `KLING_ACCESS_KEY` / `KLING_SECRET_KEY` | Kling (vídeo) |
| `STORAGE_ACCESS_KEY` / `STORAGE_SECRET_KEY` / `STORAGE_BUCKET` / `STORAGE_ENDPOINT_URL` | R2/S3 (uploads e entregáveis) |
| `JWT_SECRET` / `WEBHOOK_SIGNING_SECRET` | segredos da aplicação |

Sem as chaves de IA/storage, a API e os workers sobem e o fluxo de
créditos/jobs/idempotência roda; as chamadas de geração falham de forma controlada
(estado `FAILED` + estorno).

## Fluxo

1. Cria conta → recebe créditos de bônus.
2. Cria projeto e escolhe o estilo.
3. Envia a foto (URL assinada).
4. Dispara as etapas (avatar → história → ebook → vídeo). Cada uma debita créditos,
   enfileira um job e responde **202**; o worker processa e o front acompanha o
   progresso ao vivo.

Detalhes de arquitetura, dados, segurança/LGPD e roadmap: `backend/README.md` e os
documentos `Arquitetura_*.docx`.
