from decimal import Decimal


class SaldoInsuficienteError(Exception):
    pass


class ValorInvalidoError(Exception):
    pass


class Conta:
    def __init__(self, titular: str, saldo_inicial: Decimal):
        self.titular = titular
        self.saldo = saldo_inicial

    def debitar(self, valor: Decimal) -> None:
        if valor <= 0:
            raise ValorInvalidoError("O valor deve ser maior que zero")
        if valor > self.saldo:
            raise SaldoInsuficienteError("Saldo insuficiente")
        self.saldo -= valor

    def creditar(self, valor: Decimal) -> None:
        if valor <= 0:
            raise ValorInvalidoError("O valor deve ser maior que zero")
        self.saldo += valor