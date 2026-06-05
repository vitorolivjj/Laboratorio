# Painel v2 — migrar para build Vite

Hoje o painel é **um arquivo só** (`index.html`) usando React + Tailwind via CDN.
Funciona e é o que o FastAPI serve em `/painel`. Este guia mostra como trocar para
um **build Vite** de verdade (otimizado, sem CDN) quando você estiver numa máquina
com **Node ≥ 18**.

> O scaffold Vite (`package.json`, `vite.config.js`, `tailwind.config.js`,
> `postcss.config.js`, `src/main.jsx`, `src/index.css`) já está pronto.
> Falta só extrair o componente para `src/App.jsx` (1 passo) e buildar.

## Passo 1 — criar `src/App.jsx`

Copie **todo o conteúdo de dentro** da tag `<script type="text/babel"> … </script>`
de `index.html` para um novo `src/App.jsx` e faça 3 ajustes:

1. **Troque a 1ª linha** (`const { useState, useEffect, useRef, useCallback } = React;`)
   por um import de verdade no topo:
   ```js
   import React, { useState, useEffect, useRef, useCallback } from "react";
   ```
2. **Remova a última linha** (`ReactDOM.createRoot(...).render(<App />);`) — ela já
   está em `src/main.jsx`.
3. **Adicione no final**: `export default App;`

(O resto do código — componentes, `AGENTS`, `authFetch`, etc. — fica igual.
`React.Fragment` continua funcionando com o import acima.)

## Passo 2 — `index.html` do Vite

Troque o `index.html` por uma versão enxuta (o Vite injeta o bundle):

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Operação ao vivo — Laboratório</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
```
(guarde o `index.html` atual como `index.cdn.html` antes, se quiser o fallback CDN.)

## Passo 3 — build

```bash
cd frontend/painel-v2
npm install
npm run build      # gera dist/
npm run dev        # (opcional) dev server com hot reload
```

## Passo 4 — servir o build

No `backend/src/laboratorio/api/app.py`, aponte o mount `/painel` para o `dist/`:

```python
PAINEL_V2_DIR = REPO_ROOT / "frontend" / "painel-v2" / "dist"
```

E no deploy (`deploy/vps/`), adicione o build antes do rsync:
`cd frontend/painel-v2 && npm ci && npm run build`.

## Observações

- `.gitignore` já ignora `node_modules/` e `dist/` (padrão). Versione o `src/`.
- A migração não muda o visual nem o comportamento — só troca CDN+Babel por bundle.
- Voz por microfone (speech-to-text) não foi portada do painel clássico; a aba
  Comunicação hoje é texto + TTS. Dá pra adicionar depois com a Web Speech API.
