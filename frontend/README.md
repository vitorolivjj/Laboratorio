# Frontend — Landing TASK-001

Landing v0 para pintores autônomos. HTML estático, CTA WhatsApp only.

## Arquivos

| Arquivo | Função |
|---------|--------|
| `index.html` | Landing v0 |
| `styles.css` | Estilos responsivos |

Deploy automático: `.github/workflows/deploy-pages.yml` → GitHub Pages.

## Configurar WhatsApp (quando quiser)

Em `index.html`:

```javascript
var WHATSAPP_NUMBER = "5511999999999";  // DDI + DDD + número
var WHATSAPP_TEXT = "Oi! Vi a página de R$49 pro pintor. Quero saber como funciona.";
```

Push em `main` redeploya automaticamente.

## Testar localmente

```bash
cd frontend
python3 -m http.server 8080
# http://localhost:8080
```

## Publicar (GitHub Pages)

1. Push para `main` (dispara o workflow)
2. No GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**
3. URL: **https://vitorolivjj.github.io/Laboratorio/** ✅ (2026-05-28)

Registrar URL final em `tasks/TASK-001.md`.
