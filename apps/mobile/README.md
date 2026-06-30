# Stories Mobile (Expo)

App React Native (Expo) que espelha o fluxo do web: auth → criar projeto → enviar
foto → disparar etapas (avatar/história/ebook/vídeo) com progresso ao vivo.

## Rodar

```bash
npm install
npm start          # abre o Expo; use o app Expo Go ou um emulador
```

## Apontar para a API

Em device físico, `localhost` é o telefone — configure o IP da sua máquina em
`app.json` → `expo.extra.apiBase` (ex.: `http://192.168.0.10:8000`). No emulador
Android use `http://10.0.2.2:8000`.

## Estrutura

```
App.tsx              # alterna Auth/Studio
src/api.ts           # client REST (apiBase via expo-constants)
src/types.ts
src/AuthScreen.tsx
src/StudioScreen.tsx # projeto, expo-image-picker, etapas, progresso
```

## Typecheck

```bash
npm run typecheck
```
