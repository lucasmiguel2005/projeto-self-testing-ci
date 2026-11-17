import os
from datetime import date
from decimal import Decimal

from fastapi import FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.domain.conta import SaldoInsuficienteError, ValorInvalidoError
from src.domain.transferencia import TransferenciaInvalidaError
from src.repositories.conta_repository import (
    ContaNaoEncontradaError,
    ContaRepository,
    criar_engine_em_memoria,
)
from src.services.antifraude_client import AntiFraudeClient
from src.services.transferencia_service import ContaBloqueadaError, TransferenciaService
from src.services.validador_cadastral import ValidadorCadastral


class NovaConta(BaseModel):
    titular: str
    saldo_inicial: Decimal = Field(default=Decimal("0.00"), ge=0)


class NovaTransferencia(BaseModel):
    origem: int
    destino: int
    valor: Decimal


STATUS_POR_ERRO = {
    ContaNaoEncontradaError: 404,
    SaldoInsuficienteError: 422,
    ValorInvalidoError: 422,
    TransferenciaInvalidaError: 422,
    ContaBloqueadaError: 403,
}


def _tratador_de_erro(status: int):
    async def tratador(request: Request, exc: Exception):
        return JSONResponse(status_code=status, content={"detalhe": str(exc)})

    return tratador


def _conta_json(conta) -> dict:
    return {
        "numero": conta.numero,
        "titular": conta.titular,
        "saldo": str(conta.saldo),
    }


def criar_app(repositorio=None, antifraude=None, validador=None) -> FastAPI:
    if repositorio is None:
        repositorio = ContaRepository(criar_engine_em_memoria())
    if antifraude is None:
        antifraude = AntiFraudeClient(os.getenv("ANTIFRAUDE_URL"))
    if validador is None:
        validador = ValidadorCadastral()
    servico = TransferenciaService(repositorio, antifraude, validador)

    app = FastAPI(title="Wallet API")

    for tipo_erro, status in STATUS_POR_ERRO.items():
        app.add_exception_handler(tipo_erro, _tratador_de_erro(status))

    @app.post("/contas", status_code=201)
    def criar_conta(dados: NovaConta):
        conta = repositorio.criar(dados.titular, dados.saldo_inicial)
        return _conta_json(conta)

    @app.get("/contas/{numero}")
    def consultar_conta(numero: int):
        return _conta_json(repositorio.obter(numero))

    @app.post("/transferencias")
    def criar_transferencia(
        dados: NovaTransferencia, idempotency_key: str = Header(...)
    ):
        resultado = servico.transferir(
            idempotency_key, dados.origem, dados.destino, dados.valor
        )
        return {
            "origem": resultado["origem"],
            "destino": resultado["destino"],
            "valor": str(resultado["valor"]),
        }

    @app.get("/contas/{numero}/extrato")
    def consultar_extrato(
        numero: int,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        tipo: str | None = Query(default=None, pattern="^(debito|credito)$"),
    ):
        repositorio.obter(numero)
        itens = repositorio.extrato(numero, data_inicio, data_fim, tipo)
        return [
            {
                "tipo": item["tipo"],
                "valor": str(item["valor"]),
                "data": item["data"].isoformat(),
            }
            for item in itens
        ]

    return app