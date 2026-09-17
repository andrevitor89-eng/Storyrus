# Story R Us — Web (frontend)

Vite + React + TypeScript. Fluxo **guest-first**: o estúdio pede um JWT de
convidado (`POST /v1/auth/guest`) na primeira chamada à API → criar projeto →
upload de foto → disparar etapas (avatar/história/ebook/vídeo) com **progresso ao
vivo** via polling dos jobs.

## Rotas

`react-router-dom` separa marketing de produto (`Root.tsx`):

- `/` — **Landing** de marketing (bilíngue PT/EN). Os CTAs levam a `/app`.
- `/app` — **Estúdio** (`App` → `Studio`); sem tela de login.
- `/gastos` — painel privado de custos USD.
- `/privacidade`, `/termos` (+ aliases EN) — páginas legais.

`App`/`Studio` não dependem do router (os testes os renderizam direto). A landing
é `Landing.tsx` + `landing.css` (estilos isolados sob `.lp`, sem conflito com o
tema do estúdio em `styles.css`).

## Rodar

Na raiz do monorepo (com a API já no ar via `make up`):

```bash
make web           # npm install + vite em apps/web
```

Ou neste diretório:

```bash
npm install
npm run dev        # http://localhost:5173 (proxy /v1 e /health → :8000)
```

A API precisa estar de pé (`make up` na raiz, ou
`docker compose -f backend/docker-compose.yml up --build`). O Vite faz proxy de
`/v1` e `/health` para `VITE_API_PROXY` (default `http://localhost:8000`).

## Testes

Vitest + Testing Library + MSW (a API é mockada em memória — não chama o backend real).

```bash
npm test           # watch
npm run test:run   # uma passada (CI)
```

Cobertura dos testes:

- `App.test.tsx` — estúdio sem login → criar projeto → upload → personagem/história
  com progresso via polling; habilitar ebook após aprovar personagem.
- `Studio.test.tsx` — componentes de progresso do estúdio.
- `Usage.test.tsx` — painel `/gastos`.

Os mocks ficam em `src/test/server.ts` (handlers MSW com estado em memória que imita
projetos, jobs, guest auth e o avanço de status a cada polling).

## Estrutura

```
src/
  api.ts        # client REST (token em memória, guest JWT, Idempotency-Key por etapa)
  types.ts      # tipos compartilhados com a API
  Studio.tsx    # projeto, upload, etapas e progresso ao vivo
  App.tsx       # renderiza o Studio (guest-first)
  Landing.tsx   # landing de marketing (bilíngue PT/EN)
  landing.css   # estilos da landing, isolados sob .lp
  Usage.tsx     # painel de gastos
  Legal.tsx     # privacidade / termos
  Root.tsx      # roteamento: /, /app, /gastos, legales
  test/         # setup + servidor MSW
```
