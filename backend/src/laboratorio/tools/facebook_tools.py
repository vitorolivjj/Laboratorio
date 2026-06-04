"""Ferramentas Facebook — Chrome CDP no Mac do operador."""

from __future__ import annotations

from pydantic import BaseModel, Field

from laboratorio.social import capture, cycle, facebook_cdp, groups
from laboratorio.social.feed_analysis import extract_posts_from_feed, format_posts_report, qualify_profile_url
from laboratorio.social.facebook_cdp import (
    facebook_available,
    navigate,
    pick_facebook_page,
    page_snapshot,
    try_fill_composer,
)
from laboratorio.tools.base import BaseTool, safe


class FacebookStatusTool(BaseTool):
    name: str = "fb_status"
    description: str = (
        "Verifica se o Chrome com Facebook está conectado (CDP local). "
        "Use antes de garimpo/stalk/post."
    )

    @safe
    def _run(self) -> str:
        if not facebook_cdp.facebook_enabled():
            return "ERRO: DONIZETE_FB_ENABLED=0."
        if not facebook_cdp.cdp_reachable():
            return (
                f"ERRO: CDP offline em {facebook_cdp.CDP_URL}. "
                "Rode ./scripts/facebook-cdp-mac.sh e abra facebook.com."
            )
        try:
            with facebook_cdp.facebook_session() as browser:
                page = pick_facebook_page(browser)
                snap = page_snapshot(page)
            return f"OK — {snap.title[:60]} · {snap.url}"
        except Exception as exc:
            return f"ERRO conexão: {exc}"


class FacebookPaginaAtualTool(BaseTool):
    name: str = "fb_pagina_atual"
    description: str = "Resume texto e links visíveis na aba Facebook ativa (feed, grupo ou post)."

    @safe
    def _run(self) -> str:
        with facebook_cdp.facebook_session() as browser:
            page = pick_facebook_page(browser)
            snap = page_snapshot(page)
        excerpt = snap.text_excerpt[:2500]
        nlinks = len(snap.links)
        return (
            f"URL: {snap.url}\nTítulo: {snap.title}\nLinks FB: {nlinks}\n\n"
            f"{excerpt}"
        )


class FacebookEscolherGrupoTool(BaseTool):
    name: str = "fb_escolher_grupo"
    description: str = (
        "Donizete escolhe sozinho o próximo grupo relevante (perfil + pintura/classificados). "
        "Retorna nome e URL — use antes de navegar ou postar."
    )

    @safe
    def _run(self) -> str:
        if not groups.load_cached_groups():
            groups.list_my_groups()
        g = cycle.choose_next_group()
        return f"Escolhido: {g.name}\n{g.url}\n(Abra com fb_ciclo_navegacao ou fb_ciclo_post)"


class FacebookMeusGruposTool(BaseTool):
    name: str = "fb_meus_grupos"
    description: str = (
        "Lista grupos em que o PERFIL LOGADO participa (feed/joins do Facebook). "
        "Use ANTES de abrir grupo — não chute URL. Salva lista em cache."
    )

    @safe
    def _run(self) -> str:
        found = groups.list_my_groups()
        return groups.format_groups_list(found, title="Meus grupos (perfil)")


class _FbBuscarGruposArgs(BaseModel):
    termo: str = Field(
        ...,
        description="Busca no Facebook, ex.: classificados, pintores, bairro + cidade",
    )


class FacebookBuscarGruposTool(BaseTool):
    name: str = "fb_buscar_grupos"
    description: str = "Busca grupos no Facebook (search/groups). Não inventa slug de grupo."
    args_schema: type[BaseModel] = _FbBuscarGruposArgs

    @safe
    def _run(self, termo: str) -> str:
        found = groups.search_groups(termo)
        return groups.format_groups_list(found, title=f"Busca: {termo}")


class _FbAbrirGrupoArgs(BaseModel):
    indice: int = Field(0, description="Número na última lista (1 = primeiro)")
    nome: str = Field("", description="Trecho do nome do grupo na última lista")


class FacebookAbrirGrupoTool(BaseTool):
    name: str = "fb_abrir_grupo"
    description: str = (
        "Abre grupo da última lista (fb_meus_grupos ou fb_buscar_grupos). "
        "Use indice OU nome — nunca URL inventada."
    )
    args_schema: type[BaseModel] = _FbAbrirGrupoArgs

    @safe
    def _run(self, indice: int = 0, nome: str = "") -> str:
        idx = indice if indice and indice > 0 else None
        g = groups.open_group(indice=idx, nome=nome)
        groups.scroll_group_feed(passes=3)
        return f"Grupo aberto: {g.name}\n{g.url}\nFeed rolado — use fb_garimpo em seguida."


class FacebookRolarFeedTool(BaseTool):
    name: str = "fb_rolar_feed"
    description: str = "Rola o feed do grupo atual para carregar posts antes do garimpo."

    @safe
    def _run(self) -> str:
        return groups.scroll_group_feed()


class _FbNavegarArgs(BaseModel):
    url: str = Field(..., description="URL já conhecida (perfil/post) — NÃO para descobrir grupos")


class FacebookNavegarTool(BaseTool):
    name: str = "fb_navegar"
    description: str = (
        "Abre URL pontual (perfil/post). Para GRUPOS use fb_meus_grupos → fb_abrir_grupo."
    )
    args_schema: type[BaseModel] = _FbNavegarArgs

    @safe
    def _run(self, url: str) -> str:
        u = url.strip()
        if "/groups/" in u and "facebook.com/groups/" in u:
            cached = {g.url.rstrip("/") for g in groups.load_cached_groups()}
            norm = u.split("?")[0].rstrip("/")
            if norm not in cached and not any(norm in c for c in cached):
                return (
                    "ERRO: URL de grupo não está na lista cacheada. "
                    "Use fb_meus_grupos ou fb_buscar_grupos → fb_abrir_grupo(indice=N)."
                )
        with facebook_cdp.facebook_session() as browser:
            page = pick_facebook_page(browser)
            return navigate(page, u)


class FacebookAnalisarPostsTool(BaseTool):
    name: str = "fb_analisar_posts"
    description: str = (
        "No grupo aberto: scroll lento + lista posts com autor/perfil e sinal de pintor. "
        "Base da captação por posts existentes."
    )

    @safe
    def _run(self) -> str:
        with facebook_cdp.facebook_session() as browser:
            page = pick_facebook_page(browser)
            from laboratorio.social.feed_analysis import slow_scroll

            slow_scroll(page, passes=6)
            posts = extract_posts_from_feed(page)
            snap = page_snapshot(page)
        grupo = snap.url
        return format_posts_report(posts, grupo)


class _FbQualificarArgs(BaseModel):
    perfil_url: str = Field(..., description="URL do perfil do autor do post")


class FacebookQualificarPerfilTool(BaseTool):
    name: str = "fb_qualificar_perfil"
    description: str = (
        "Visita perfil do autor do post, analisa se é pintor (lead) ou pedido de indicação (descartar)."
    )
    args_schema: type[BaseModel] = _FbQualificarArgs

    @safe
    def _run(self, perfil_url: str) -> str:
        ok, motivo, sc = qualify_profile_url(perfil_url)
        return f"qualificado={ok} score={sc} motivo={motivo} url={perfil_url}"


class FacebookCicloNavegacaoTool(BaseTool):
    name: str = "fb_ciclo_navegacao"
    description: str = (
        "Atuação NAVEGAÇÃO: escolhe grupo → scroll lento → analisa posts → "
        "visita perfil → stalk se lead. Um lead por ciclo."
    )

    @safe
    def _run(self) -> str:
        return cycle.run_navigation_cycle(max_leads=1)


class FacebookCicloPostTool(BaseTool):
    name: str = "fb_ciclo_post"
    description: str = (
        "Atuação POST: Donizete escolhe grupo e PUBLICA post-isca (autorizado)."
    )

    @safe
    def _run(self) -> str:
        return cycle.run_post_cycle()


class FacebookGarimpoTool(BaseTool):
    name: str = "fb_garimpo"
    description: str = "Garimpo rápido na tela atual (preferir fb_analisar_posts no grupo)."

    @safe
    def _run(self) -> str:
        return capture.run_garimpo()


class _FbStalkArgs(BaseModel):
    perfil_url: str = Field(..., description="URL do perfil Facebook")
    nome: str = Field(..., description="Nome do pintor")
    cidade: str = Field("", description="Cidade se visível")
    grupo_origem: str = Field("", description="Grupo onde foi visto")
    tags: str = Field("autopromocao", description="indicacao | autopromocao")
    contato: str = Field("", description="WhatsApp público se houver")
    observacoes: str = Field("", description="Resumo do que publicou")


class FacebookStalkTool(BaseTool):
    name: str = "fb_stalk"
    description: str = (
        "Abre perfil, salva screenshot e imagens em captura/raw, "
        "cria lead no CRM LP. Com ≥3 imagens → pronto_pra_pagina."
    )
    args_schema: type[BaseModel] = _FbStalkArgs

    @safe
    def _run(self, **kwargs) -> str:
        return capture.stalk_profile(**kwargs)


class _FbPostIscaArgs(BaseModel):
    texto: str = Field(..., description="Texto do post-isca (variação do plano)")
    confirmar_publicacao: bool = Field(
        True,
        description="True = publica no grupo (Vitor autorizou). False = só cola rascunho",
    )


class FacebookPostIscaTool(BaseTool):
    name: str = "fb_post_isca"
    description: str = (
        "Post-isca no grupo aberto. Vitor autorizou publicação — confirmar_publicacao=True por padrão."
    )
    args_schema: type[BaseModel] = _FbPostIscaArgs

    @safe
    def _run(self, texto: str, confirmar_publicacao: bool = False) -> str:
        with facebook_cdp.facebook_session() as browser:
            page = pick_facebook_page(browser)
            return try_fill_composer(page, texto, submit=confirmar_publicacao)


def facebook_tools_available() -> bool:
    return facebook_available()
