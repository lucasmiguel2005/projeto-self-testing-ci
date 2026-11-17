from decimal import Decimal

from src.domain.conta import Conta
from src.services.transferencia_service import TransferenciaService


class RepositorioFalso:
    def __init__(self, contas):
        self._contas = contas

    def obter(self, numero):
        return self._contas[numero]

    def registrar_transferencia(self, origem, destino, valor):
        pass


def montar_cenario():
    ana = Conta("Ana", Decimal("100.00"))
    bruno = Conta("Bruno", Decimal("50.00"))
    servico = TransferenciaService(RepositorioFalso({"ana": ana, "bruno": bruno}))
    return ana, bruno, servico


def test_transferir_move_o_dinheiro():
    ana, bruno, servico = montar_cenario()

    servico.transferir("chave-1", "ana", "bruno", Decimal("30.00"))

    assert ana.saldo == Decimal("70.00")
    assert bruno.saldo == Decimal("80.00")


def test_repetir_a_mesma_chave_nao_transfere_duas_vezes():
    ana, bruno, servico = montar_cenario()

    primeiro = servico.transferir("chave-1", "ana", "bruno", Decimal("30.00"))
    segundo = servico.transferir("chave-1", "ana", "bruno", Decimal("30.00"))

    assert ana.saldo == Decimal("70.00")
    assert bruno.saldo == Decimal("80.00")
    assert segundo == primeiro