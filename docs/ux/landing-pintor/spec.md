# LP Pintor — Spec UX (v1 vitrine)

**Task:** LP-PINTOR-002 · **Agente:** Loide · **Status:** v1 mínimo (1 modelo × 2 temas; expandir para 2×4)

## Modelos (roadmap)

| ID | Nome | Uso |
|----|------|-----|
| `classico` | Hero + serviços + galeria + CTA WA | **v1 implementado** |
| `compacto` | Uma dobra + galeria | v2 |

## Temas (v1: 2 de 4)

| ID | Paleta | Perfil |
|----|--------|--------|
| `azul` | Navy + laranja CTA | Profissional, confiança |
| `verde` | Verde obra + branco | Obra, prático |

## Campos editáveis (handoff Donizete → Loide)

- Nome / negócio
- Cidade
- Tipo de serviço
- WhatsApp + texto CTA
- 2–6 fotos (URLs ou paths locais no build)

## Build

```bash
./scripts/lp-pintor-build.sh leads/exemplo
./scripts/lp-pintor-deploy.sh leads/exemplo   # Surge ou pasta dist/
```

## Critério v1

Prévia publicável em minutos a partir de `config.json` — suficiente para vitrine e LEAD-001.
