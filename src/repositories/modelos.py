from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ContaModel(Base):
    __tablename__ = "contas"

    numero: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titular: Mapped[str] = mapped_column(String, nullable=False)
    saldo_centavos: Mapped[int] = mapped_column(Integer, nullable=False)


class TransacaoModel(Base):
    __tablename__ = "transacoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conta_numero: Mapped[int] = mapped_column(ForeignKey("contas.numero"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    valor_centavos: Mapped[int] = mapped_column(Integer, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)