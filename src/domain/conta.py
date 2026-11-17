from decimal import Decimal


class SaldoInsuficienteError(Exception):
    pass


class ValorInvalidoError(Exception):
    pass


class Conta:
    def __init__(self, titular: str, saldo_inicial: Decimal, numero: int | None = None):
        self.titular = titular
        self.saldo = saldo_inicial
        self.numero = numero

    def debitar(self, valor: Decimal) -> None:
        self._validar_valor(valor)
        if valor > self.saldo:
            raise SaldoInsuficienteError("Saldo insuficiente")
        self.saldo -= valor

    def creditar(self, valor: Decimal) -> None:
        self._validar_valor(valor)
        self.saldo += valor

    @staticmethod
    def _validar_valor(valor: Decimal) -> None:
        if valor <= 0:
            raise ValorInvalidoError("O valor deve ser maior que zero")