from decimal import Decimal

from src.domain.conta import Conta


class TransferenciaInvalidaError(Exception):
    pass


def transferir(origem: Conta, destino: Conta, valor: Decimal) -> None:
    if origem is destino:
        raise TransferenciaInvalidaError("Origem e destino devem ser contas diferentes")
    origem.debitar(valor)
    destino.creditar(valor)