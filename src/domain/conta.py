from decimal import Decimal


class SaldoInsuficienteError(Exception):
    pass


class Conta:
    def __init__(self, titular: str, saldo_inicial: Decimal):
        self.titular = titular
        self.saldo = saldo_inicial

    def debitar(self, valor: Decimal) -> None:
        if valor > self.saldo:
            raise SaldoInsuficienteError("Saldo insuficiente")
        self.saldo -= valor