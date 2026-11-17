from decimal import Decimal

import pytest

from src.domain.conta import Conta, SaldoInsuficienteError
from src.domain.transferencia import TransferenciaInvalidaError, transferir


def test_transferir_move_o_dinheiro_entre_as_contas():
    ana = Conta("Ana", Decimal("100.00"))
    bruno = Conta("Bruno", Decimal("50.00"))

    transferir(ana, bruno, Decimal("30.00"))

    assert ana.saldo == Decimal("70.00")
    assert bruno.saldo == Decimal("80.00")


def test_saldo_insuficiente_nao_altera_nenhuma_das_contas():
    ana = Conta("Ana", Decimal("20.00"))
    bruno = Conta("Bruno", Decimal("50.00"))

    with pytest.raises(SaldoInsuficienteError):
        transferir(ana, bruno, Decimal("30.00"))

    assert ana.saldo == Decimal("20.00")
    assert bruno.saldo == Decimal("50.00")


def test_nao_transfere_para_a_mesma_conta():
    ana = Conta("Ana", Decimal("100.00"))

    with pytest.raises(TransferenciaInvalidaError):
        transferir(ana, ana, Decimal("10.00"))

    assert ana.saldo == Decimal("100.00")