"""Ferramentas de captação — Ronaldo sugere células (segmento × área)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from laboratorio.tools.base import BaseTool, safe


class _SugerirCelulaArgs(BaseModel):
    segmento: str = Field(..., description=(
        "Segmento do ICP, ex.: 'clínica odontológica', 'escritório de advocacia', "
        "'oficina mecânica', 'imobiliária', 'clínica veterinária'"))
    area: str = Field(..., description=(
        "Área geográfica: cidade pequena/média inteira (ex.: 'Contagem MG') ou "
        "bairro em capital (ex.: 'Savassi, Belo Horizonte')"))
    motivo: str = Field("", description="Por que esta célula agora (1 frase)")


class SugerirCelulaTool(BaseTool):
    name: str = "sugerir_celula_captacao"
    description: str = (
        "Sugere uma CÉLULA de captação (segmento × área) para o Vitor aprovar. "
        "Aprovada, o Donizete varre o Google Maps da célula e registra os leads "
        "6+ no CRM. Use os segmentos prioritários do ICP e áreas ainda não "
        "varridas (memoria/captacao_celulas.md)."
    )
    args_schema: type[BaseModel] = _SugerirCelulaArgs

    @safe
    def _run(self, segmento: str, area: str, motivo: str = "") -> str:
        from laboratorio.ops.captacao import celulas_varridas
        from laboratorio.whatsapp.approvals import request_celula_captacao

        key = f"{segmento}|{area}".strip().lower()
        if key in celulas_varridas():
            return f"Célula '{segmento} em {area}' já foi varrida — sugira outra."
        aid = request_celula_captacao(segmento, area, motivo=motivo)
        return (f"Célula sugerida ao Vitor (aprovação {aid}): {segmento} em {area}. "
                "Aguardando APROVAR.")
