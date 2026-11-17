from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.domain.conta import Conta
from src.repositories.modelos import Base, ContaModel, TransacaoModel


class ContaNaoEncontradaError(Exception):
    pass


def criar_engine_em_memoria():
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _para_centavos(valor: Decimal) -> int:
    return int(valor * 100)


def _para_decimal(centavos: int) -> Decimal:
    return (Decimal(centavos) / 100).quantize(Decimal("0.01"))


class ContaRepository:
    def __init__(self, engine):
        Base.metadata.create_all(engine)
        self._sessoes = sessionmaker(bind=engine, expire_on_commit=False)

    def criar(self, titular: str, saldo_inicial: Decimal) -> Conta:
        with self._sessoes() as sessao:
            modelo = ContaModel(
                titular=titular, saldo_centavos=_para_centavos(saldo_inicial)
            )
            sessao.add(modelo)
            sessao.commit()
            return self._para_dominio(modelo)

    def obter(self, numero: int) -> Conta:
        with self._sessoes() as sessao:
            modelo = sessao.get(ContaModel, numero)
            if modelo is None:
                raise ContaNaoEncontradaError(f"Conta {numero} não encontrada")
            return self._para_dominio(modelo)

    def registrar_transferencia(
        self, origem: Conta, destino: Conta, valor: Decimal
    ) -> None:
        agora = datetime.now()
        with self._sessoes() as sessao:
            sessao.get(ContaModel, origem.numero).saldo_centavos = _para_centavos(
                origem.saldo
            )
            sessao.get(ContaModel, destino.numero).saldo_centavos = _para_centavos(
                destino.saldo
            )
            sessao.add(
                TransacaoModel(
                    conta_numero=origem.numero,
                    tipo="debito",
                    valor_centavos=_para_centavos(valor),
                    criado_em=agora,
                )
            )
            sessao.add(
                TransacaoModel(
                    conta_numero=destino.numero,
                    tipo="credito",
                    valor_centavos=_para_centavos(valor),
                    criado_em=agora,
                )
            )
            sessao.commit()

    def extrato(
        self,
        numero: int,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        tipo: str | None = None,
    ) -> list[dict]:
        consulta = select(TransacaoModel).where(TransacaoModel.conta_numero == numero)
        if tipo:
            consulta = consulta.where(TransacaoModel.tipo == tipo)
        if data_inicio:
            inicio = datetime.combine(data_inicio, time.min)
            consulta = consulta.where(TransacaoModel.criado_em >= inicio)
        if data_fim:
            fim = datetime.combine(data_fim, time.max)
            consulta = consulta.where(TransacaoModel.criado_em <= fim)
        consulta = consulta.order_by(TransacaoModel.id)

        with self._sessoes() as sessao:
            return [
                {
                    "tipo": t.tipo,
                    "valor": _para_decimal(t.valor_centavos),
                    "data": t.criado_em,
                }
                for t in sessao.scalars(consulta)
            ]

    @staticmethod
    def _para_dominio(modelo: ContaModel) -> Conta:
        return Conta(
            titular=modelo.titular,
            saldo_inicial=_para_decimal(modelo.saldo_centavos),
            numero=modelo.numero,
        )