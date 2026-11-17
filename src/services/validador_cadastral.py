class ValidadorCadastral:
    """Consulta (fictícia) ao cadastro externo: toda conta é considerada regular."""

    def conta_regular(self, numero: int) -> bool:
        return True