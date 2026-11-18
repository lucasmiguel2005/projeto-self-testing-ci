from decimal import Decimal

from src.domain.transferencia import TransferenciaInvalidaError, transferir


class ContaBloqueadaError(Exception):
    pass


class TransferenciaService:
    def __init__(self, repositorio, antifraude=None, validador_cadastral=None):
        self._repositorio = repositorio
        self._antifraude = antifraude
        self._validador = validador_cadastral
        self._processadas = {}

    def transferir(
        self, chave: str, origem_id, destino_id, valor: Decimal
    ) -> dict:
        if chave in self._processadas:
            return self._processadas[chave]

        if origem_id == destino_id:
            raise TransferenciaInvalidaError(
                "Origem e destino devem ser contas diferentes"
            )
        self._validar_cadastro(origem_id, destino_id)

        origem = self._repositorio.obter(origem_id)
        destino = self._repositorio.obter(destino_id)

        transferir(origem, destino, valor)

        self._repositorio.registrar_transferencia(origem, destino, valor)
        self._notificar_antifraude(chave, origem_id, destino_id, valor)

        resultado = {"origem": origem_id, "destino": destino_id, "valor": valor}
        self._processadas[chave] = resultado
        return resultado

    def _validar_cadastro(self, *numeros) -> None:
        if self._validador is None:
            return
        for numero in numeros:
            if not self._validador.conta_regular(numero):
                raise ContaBloqueadaError(f"Conta {numero} com cadastro irregular")

    def _notificar_antifraude(self, chave, origem_id, destino_id, valor) -> None:
        if self._antifraude is None:
            return
        self._antifraude.notificar(
            {
                "chave": chave,
                "origem": origem_id,
                "destino": destino_id,
                "valor": str(valor),
            }
        )