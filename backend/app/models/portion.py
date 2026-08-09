from __future__ import annotations

from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Portion(Base):
    """Conversão determinística de unidade caseira para gramas.

    Substitui a constante textual `_PORTIONS_REF`, que vivia embutida no prompt
    do Estágio 1 e dependia do conhecimento livre do modelo para converter
    "8 fatias" em gramas (bug 001, achado A).

    O casamento é por `term`: o termo é procurado dentro do nome do alimento
    normalizado (minúsculas, sem acento). Entre vários candidatos vence o de
    maior `priority` e, empatado, o de `term` mais longo — assim
    "pao de forma" ganha de "pao" para a unidade "fatia".

    `grams_min`/`grams_max` delimitam a faixa plausível e alimentam a checagem
    de porção do pipeline: uma quantidade fora da faixa marca o item como baixa
    confiança em vez de ser aceita em silêncio.
    """

    __tablename__ = "portions"
    __table_args__ = (UniqueConstraint("term", "unit", name="uq_portions_term_unit"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Termo procurado dentro do nome do alimento (minúsculo, sem acento).
    # Vazio ("") = regra genérica, vale para qualquer alimento naquela unidade.
    term: Mapped[str] = mapped_column(String(80), index=True)
    # Unidade caseira normalizada — ver UNIDADES em services/nutrition/portions.py
    unit: Mapped[str] = mapped_column(String(30), index=True)

    grams: Mapped[float] = mapped_column(Float)
    grams_min: Mapped[float] = mapped_column(Float)
    grams_max: Mapped[float] = mapped_column(Float)

    # Desempate entre regras que casam o mesmo alimento (maior vence)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    # Procedência declarada do número — auditabilidade é requisito, não enfeite
    source: Mapped[str] = mapped_column(String(120))

    def __repr__(self) -> str:
        return f"<Portion {self.term!r} 1 {self.unit} = {self.grams}g>"
