from decimal import Decimal

from src.domain.transferencia import transferir


class TransferenciaService:
    def __init__(self, repositorio):
        self._repositorio = repositorio
        self._processadas = {}

    def transferir(self, chave: str, origem_id: str, destino_id: str, valor: Decimal) -> dict:
        if chave in self._processadas:
            return self._processadas[chave]

        origem = self._repositorio.obter(origem_id)
        destino = self._repositorio.obter(destino_id)

        transferir(origem, destino, valor)

        self._repositorio.salvar(origem)
        self._repositorio.salvar(destino)

        resultado = {"origem": origem_id, "destino": destino_id, "valor": valor}
        self._processadas[chave] = resultado
        return resultado