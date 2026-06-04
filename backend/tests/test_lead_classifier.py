"""Testes classificação lead Donizete LP."""

from laboratorio.social.lead_classifier import classify_text, should_register_lead


def test_pintor_oferece_servico():
    c = classify_text("Faço pintura residencial e comercial. Chama no zap.", nome="João Pinturas")
    assert c.is_lead
    assert c.tier in ("quente", "medio")
    assert c.oferece_servico


def test_cliente_procurando_nao_lead():
    c = classify_text("Preciso de pintor para minha casa, quem indica?")
    assert not c.is_lead
    assert c.tier == "nao_lead"


def test_loja_tinta_nao_lead():
    c = classify_text("Promoção de tinta na loja, vendemos massa corrida")
    assert not c.is_lead


def test_painel_tv_nao_lead():
    c = classify_text("Painel luminoso de TV com acabamento", nome="Bio construções")
    assert not c.is_lead


def test_should_register_fraco_pintor_nome():
    assert should_register_lead("Trabalhos de pintura", nome="Carlos Pintor")
