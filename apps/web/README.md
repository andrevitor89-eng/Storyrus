# Stories Web (frontend)

Vite + React + TypeScript. Fluxo: login/signup → criar projeto → upload de foto →
escolher estilo → disparar etapas (avatar/história/ebook/vídeo) com **progresso ao
vivo** via polling dos jobs.

## Rotas

`react-router-dom` separa marketing de produto:

- `/` — **Landing** de marketing (bilíngue PT/EN, tema mágico). Os CTAs levam a `/app`.
- `/app` — **App** do produto: `Auth` → `Studio`.

`App`/`Auth`/`Studio` não dependem do router (os testes os renderizam direto). O
roteamento vive em `Root.tsx`; a landing é `Landing.tsx` + `landing.css` (estilos
isolados sob `.lp`, sem conflito com o tema escuro do estúdio em `styles.css`).

## Rodar

```bash
npm install
npm run dev        # http://localhost:5173 (proxy /v1 -> http://localhost:8000)
```

A API precisa estar de pé (`cd ../../backend && docker compose up`).

## Testes

Vitest + Testing Library + MSW (a API é mockada em memória — não chama o backend real).

```bash
npm test           # watch
npm run test:run   # uma passada (CI)
```

Cobertura dos testes:

- `Auth.test.tsx` — signup com sucesso; erro de credenciais no login.
- `App.test.tsx` (E2E) — signup → criar projeto → upload → disparar história →
  progresso `PENDING → RUNNING → DONE` → história exibida → crédito debitado (10→9);
  bloqueio de "gerar personagem" sem foto; logout volta ao login.

Os mocks ficam em `src/test/server.ts` (handlers MSW com estado em memória que imita
projetos, jobs e o avanço de status a cada polling).

## Estrutura

```
src/
  api.ts        # client REST (token em memória, Idempotency-Key por etapa)
  types.ts      # tipos compartilhados com a API
  Auth.tsx      # login/signup
  Studio.tsx    # projeto, upload, etapas e progresso ao vivo
  App.tsx       # alterna Auth/Studio
  Landing.tsx   # landing de marketing (bilíngue PT/EN)
  landing.css   # estilos da landing, isolados sob .lp
  Root.tsx      # roteamento: / (Landing) e /app (App)
  test/         # setup + servidor MSW
```
