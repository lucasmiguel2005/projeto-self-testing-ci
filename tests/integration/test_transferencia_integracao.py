from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.domain.conta import SaldoInsuficienteError
from src.domain.transferencia import TransferenciaInvalidaError
from src.repositories.conta_repository import (
    ContaNaoEncontradaError,
    ContaRepository,
    criar_engine_em_memoria,
)
from src.services.antifraude_client import AntiFraudeClient
from src.services.transferencia_service import ContaBloqueadaError, TransferenciaService


class ValidadorCadastralStub:
    """Stub: responde de forma fixa, só para controlar o cenário do teste."""

    def __init__(self, contas_irregulares=()):
        self._irregulares = set(contas_irregulares)

    def conta_regular(self, numero):
        return numero not in self._irregulares


@pytest.fixture
def repositorio():
    return ContaRepository(criar_engine_em_memoria())


@pytest.fixture
def antifraude():
    return Mock(spec=AntiFraudeClient)


@pytest.fixture
def servico(repositorio, antifraude):
    return TransferenciaService(repositorio, antifraude, ValidadorCadastralStub())


def test_transferencia_persiste_os_saldos_no_banco(repositorio, servico):
    ana = repositorio.criar("Ana", Decimal("100.00"))
    bruno = repositorio.criar("Bruno", Decimal("50.00"))

    servico.transferir("chave-1", ana.numero, bruno.numero, Decimal("30.00"))

    assert repositorio.obter(ana.numero).saldo == Decimal("70.00")
    assert repositorio.obter(bruno.numero).saldo == Decimal("80.00")


def test_notifica_o_antifraude_uma_vez_com_os_dados_da_transferencia(
    repositorio, servico, antifraude
):
    ana = repositorio.criar("Ana", Decimal("100.00"))
    bruno = repositorio.criar("Bruno", Decimal("50.00"))

    servico.transferir("chave-1", ana.numero, bruno.numero, Decimal("30.00"))

    antifraude.notificar.assert_called_once_with(
        {
            "chave": "chave-1",
            "origem": ana.numero,
            "destino": bruno.numero,
            "valor": "30.00",
        }
    )


def test_chave_repetida_nao_transfere_nem_notifica_de_novo(
    repositorio, servico, antifraude
):
    ana = repositorio.criar("Ana", Decimal("100.00"))
    bruno = repositorio.criar("Bruno", Decimal("50.00"))

    servico.transferir("chave-1", ana.numero, bruno.numero, Decimal("30.00"))
    servico.transferir("chave-1", ana.numero, bruno.numero, Decimal("30.00"))

    assert antifraude.notificar.call_count == 1
    assert repositorio.obter(ana.numero).saldo == Decimal("70.00")
    assert repositorio.obter(bruno.numero).saldo == Decimal("80.00")


def test_saldo_insuficiente_nao_notifica_e_nao_altera_o_banco(
    repositorio, servico, antifraude
):
    ana = repositorio.criar("Ana", Decimal("20.00"))
    bruno = repositorio.criar("Bruno", Decimal("50.00"))

    with pytest.raises(SaldoInsuficienteError):
        servico.transferir("chave-1", ana.numero, bruno.numero, Decimal("30.00"))

    antifraude.notificar.assert_not_called()
    assert repositorio.obter(ana.numero).saldo == Decimal("20.00")
    assert repositorio.obter(bruno.numero).saldo == Decimal("50.00")


def test_conta_com_cadastro_irregular_bloqueia_a_transferencia(
    repositorio, antifraude
):
    ana = repositorio.criar("Ana", Decimal("100.00"))
    bruno = repositorio.criar("Bruno", Decimal("50.00"))
    validador = ValidadorCadastralStub(contas_irregulares={bruno.numero})
    servico = TransferenciaService(repositorio, antifraude, validador)

    with pytest.raises(ContaBloqueadaError):
        servico.transferir("chave-1", ana.numero, bruno.numero, Decimal("30.00"))

    antifraude.notificar.assert_not_called()
    assert repositorio.obter(ana.numero).saldo == Decimal("100.00")


def test_nao_transfere_para_a_mesma_conta_pelo_servico(repositorio, servico):
    ana = repositorio.criar("Ana", Decimal("100.00"))

    with pytest.raises(TransferenciaInvalidaError):
        servico.transferir("chave-1", ana.numero, ana.numero, Decimal("10.00"))

    assert repositorio.obter(ana.numero).saldo == Decimal("100.00")


def test_extrato_lista_debito_e_credito_e_aceita_filtros(repositorio, servico):
    ana = repositorio.criar("Ana", Decimal("100.00"))
    bruno = repositorio.criar("Bruno", Decimal("50.00"))
    servico.transferir("c1", ana.numero, bruno.numero, Decimal("30.00"))
    servico.transferir("c2", bruno.numero, ana.numero, Decimal("10.00"))

    todos = repositorio.extrato(ana.numero)
    assert [(t["tipo"], t["valor"]) for t in todos] == [
        ("debito", Decimal("30.00")),
        ("credito", Decimal("10.00")),
    ]

    so_debitos = repositorio.extrato(ana.numero, tipo="debito")
    assert [t["valor"] for t in so_debitos] == [Decimal("30.00")]

    hoje = date.today()
    assert len(repositorio.extrato(ana.numero, data_inicio=hoje, data_fim=hoje)) == 2
    assert repositorio.extrato(ana.numero, data_inicio=hoje + timedelta(days=1)) == []


def test_conta_inexistente_levanta_erro(repositorio):
    with pytest.raises(ContaNaoEncontradaError):
        repositorio.obter(999)