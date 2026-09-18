# Story R Us — Mobile (Expo)

App React Native (Expo) que espelha o fluxo do web: **guest-first** → temas /
nome → criar projeto → consentimento + foto → etapas (avatar, história, ebook,
vídeo, **vídeo narrado**) → vozes, aprovações e pedido de impressão. Login/signup
é opcional (botão "Entrar" no estúdio).

## Rodar

```bash
npm install
npm start          # abre o Expo; use o app Expo Go ou um emulador
```

## Apontar para a API

Por padrão `expo.extra.apiBase` aponta para o BFF de produção
`https://storyrus.ai` (API sob `/v1`, same-origin proxy).

Para desenvolvimento local, sobrescreva com a env `EXPO_PUBLIC_API_BASE`
(tem prioridade sobre `app.json`):

```bash
# Emulador Android → host machine
EXPO_PUBLIC_API_BASE=http://10.0.2.2:8000 npx expo start

# Device físico → IP da sua máquina na LAN
EXPO_PUBLIC_API_BASE=http://192.168.0.10:8000 npx expo start
```

Ou edite temporariamente `app.json` → `expo.extra.apiBase`.

O JWT (guest ou conta) é persistido em AsyncStorage (`storyrus_token`).

## Estrutura

```
App.tsx              # boot guest → Studio; Auth opcional
src/api.ts           # client REST + ensureGuest + AsyncStorage
src/types.ts
src/themes.ts        # catálogo de temas (paridade web)
src/AuthScreen.tsx   # login/signup opcional
src/StudioScreen.tsx # temas, etapas, aprovações, assets
src/VoicePanel.tsx   # clone / seleção de voz (narrated-video)
```

Ainda fora desta fatia (follow-ups): personagens extras, templates de história,
i18n do estúdio mobile, galeria rica de páginas.

## Typecheck

```bash
npm run typecheck
```

## Publicar (EAS / lojas)

Builds e submit via Expo Application Services: ver **[PUBLISH.md](./PUBLISH.md)**
(`eas.json`, perfis `preview` / `production`, checklist de segredos).

```bash
# após eas login + eas init (uma vez)
npm run eas:build:preview -- --platform android
```
