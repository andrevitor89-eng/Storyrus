# Plataforma de Histórias — API (núcleo)

MVP do backend: **foto → personagem → ebook → vídeo animado**. Pipeline assíncrono com
créditos, jobs idempotentes, moderação/segurança e clients reais de IA (Nano Banana —
Gemini 2.5 Flash Image, Claude, Kling). FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL.

## Estrutura

```
backend/
  app/
    config.py            # settings via ambiente (12-factor)
    database.py          # engine/sessão SQLAlchemy
    models.py            # users, projects, jobs, assets (UUID/JSON portáveis)
    schemas.py           # DTOs Pydantic v2
    security.py          # hash de senha + JWT
    deps.py              # usuário autenticado
    storage.py           # URLs assinadas S3/R2
    services/
      credits.py         # débito/estorno com lock de linha
      jobs.py            # enfileiramento idempotente + backpressure + custo
    routers/
      auth.py credits.py projects.py jobs.py webhooks.py
    ai_clients/
      base.py            # interfaces ImageProvider/TextProvider/VideoProvider
      image_nano_banana.py  text_anthropic.py  video_kling.py  factory.py
    workers/
      runner.py          # loop: claim + retry/backoff + estorno
      handlers.py        # AVATAR/STORY/EBOOK/STORYBOARD/VIDEO
      ebook.py           # montagem HTML -> PDF
  alembic/               # migrations
  tests/                 # pytest (SQLite em memória)
  Dockerfile  docker-compose.yml  pyproject.toml  .env.example
```

## Rodar local (Docker)

```bash
cp .env.example .env          # preencha as chaves de IA
docker compose up --build     # sobe Postgres + Redis + API (migra automático)
# Swagger: http://localhost:8000/docs
```

## Rodar local (sem Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Testes

```bash
pytest            # usa SQLite em memória; não chama provedores externos
```

## Fluxo da API (resumo)

1. `POST /v1/auth/signup` → token JWT (+ créditos de bônus).
2. `POST /v1/projects` → cria projeto (`style`: realistic|cartoon|anime).
3. `POST /v1/projects/{id}/photos` → URL assinada para upload da foto.
4. `POST /v1/projects/{id}/avatar|story|ebook|video` → **202 Accepted** com `job_id`.
   Envie `Idempotency-Key` para evitar duplicar custo.
5. `GET /v1/jobs/{id}` → polling do estado. Vídeo conclui via `POST /v1/webhooks/video`
   (callback assinado por HMAC).

## Decisões de engenharia

- **Crédito debitado antes** da etapa paga; **estorno automático** em falha definitiva.
- **Idempotência** por `Idempotency-Key` única em `jobs`.
- **Backpressure**: `MAX_CONCURRENT_JOBS_PER_USER` (default 4). VIDEO não entra nessa
  contagem — fica RUNNING por muito tempo (polling + retries) e travava outras ações
  do usuário com 429 enquanto um vídeo ainda gerava.
- **Consistência de personagem**: `character_ref` é reutilizada em todas as cenas.
- **Segurança/LGPD**: chaves só no backend, entregáveis via URL assinada de curta duração,
  callbacks validados por assinatura.
- **Troca de provedor** sem reescrever o fluxo: tudo atrás de `ai_clients` (factory).

## Workers (pipeline)

Os endpoints registram jobs `PENDING`; o worker os consome e executa as etapas.

```bash
python -m app.workers.runner     # local
# ou: docker compose up worker
```

Runner (`app/workers/runner.py`):

- **claim** do próximo `PENDING` com `FOR UPDATE SKIP LOCKED` (vários workers em paralelo).
- **retry** com backoff exponencial só em erro transitório (429/5xx/timeout).
- ao esgotar `JOB_MAX_ATTEMPTS` → `FAILED` + **estorno** de créditos.

Handlers (`app/workers/handlers.py`):

- `AVATAR` gera o personagem e grava `character_ref` (reusado em todas as cenas).
- `STORY` gera o texto (Claude).
- `EBOOK` ilustra cada página reusando o personagem e monta o PDF.
- `STORYBOARD` gera keyframes; `VIDEO` dispara o Kling e faz polling até concluir
  (ou conclui via webhook), republicando o arquivo no storage próprio.
