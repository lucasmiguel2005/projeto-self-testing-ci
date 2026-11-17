from decimal import Decimal

import pytest

from src.domain.conta import Conta, SaldoInsuficienteError


def test_conta_nova_comeca_com_o_saldo_inicial():
    conta = Conta(titular="Ana", saldo_inicial=Decimal("100.00"))

    assert conta.saldo == Decimal("100.00")


def test_debitar_reduz_o_saldo():
    conta = Conta(titular="Ana", saldo_inicial=Decimal("100.00"))

    conta.debitar(Decimal("30.00"))

    assert conta.saldo == Decimal("70.00")


def test_nao_deixa_debitar_mais_que_o_saldo():
    conta = Conta(titular="Ana", saldo_inicial=Decimal("50.00"))

    with pytest.raises(SaldoInsuficienteError):
        conta.debitar(Decimal("80.00"))

    assert conta.saldo == Decimal("50.00")