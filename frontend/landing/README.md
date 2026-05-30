# Landing TASK-001 — Pintores autônomos

Landing v0 para pintores autônomos. HTML estático, CTA WhatsApp only.

> **Deploy:** não vai para GitHub Pages (domínio reservado ao site institucional).  
> Use Vercel, Netlify ou outro host para URL pública da landing.

## Arquivos

| Arquivo | Função |
|---------|--------|
| `index.html` | Landing v0 |
| `styles.css` | Estilos responsivos |

## Configurar WhatsApp

Em `index.html`:

```javascript
var WHATSAPP_NUMBER = "5511999999999";
var WHATSAPP_TEXT = "Oi! Vi a página de R$49 pro pintor. Quero saber como funciona.";
```

## Testar localmente

```bash
cd frontend/landing
python3 -m http.server 8080
# http://localhost:8080
```
