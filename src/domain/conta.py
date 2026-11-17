from decimal import Decimal


class Conta:
    def __init__(self, titular: str, saldo_inicial: Decimal):
        self.titular = titular
        self.saldo = saldo_inicial