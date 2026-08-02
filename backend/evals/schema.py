"""Contrato de um caso de avaliação.

O schema carrega a **procedência** de cada número de referência (`fonte_referencia`
+ `fonte_url`) para que um terceiro consiga auditar a métrica sem confiar no
projeto. É também o que torna o harness agnóstico à decisão da OQ2.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

DATASET_DIR = Path(__file__).parent / "dataset"
CASOS_PATH = DATASET_DIR / "casos.jsonl"

#: Fontes proibidas como referência, por circularidade: derivar o ground truth
#: da tabela de porções do próprio projeto faria a métrica medir a tabela contra
#: si mesma. O docstring de `scripts/eval_golden_set.py:20-27` identificou isso
#: primeiro; aqui vira regra de validação.
FONTES_PROIBIDAS = ("portions", "portion", "tabela de porcoes", "tabela de porções")


class Estrato(StrEnum):
    SIMPLES = "simples"
    COMPOSTO = "composto"
    FOTO = "foto"


class MacrosReferencia(BaseModel):
    """Macros de referência da porção inteira, em gramas."""

    proteina_g: float = Field(ge=0)
    carboidrato_g: float = Field(ge=0)
    gordura_g: float = Field(ge=0)
    fibra_g: float | None = Field(default=None, ge=0)


class CasoEval(BaseModel):
    """Um caso do dataset de avaliação."""

    model_config = {"extra": "forbid"}

    id: str = Field(min_length=1)
    estrato: Estrato
    descricao: str = Field(min_length=1)
    referencia_kcal: float = Field(gt=0)
    referencia_macros: MacrosReferencia | None = None
    fonte_referencia: str = Field(min_length=1)
    fonte_url: str = Field(min_length=1)
    grupo_invariancia: str | None = None
    data_de_adicao: date
    #: `False` enquanto o valor não foi conferido contra a publicação da fonte.
    #: Os casos-semente da fase C.3 nascem `False` por honestidade; a C.4 vira
    #: para `True` ao confirmar cada número na fonte citada.
    verificada: bool = False
    #: Caminho da imagem, relativo a `evals/dataset/`. Obrigatório no estrato
    #: `foto` — sem imagem o caso não é executável.
    imagem_path: str | None = None
    notas: str = ""

    @field_validator("fonte_referencia")
    @classmethod
    def _fonte_nao_pode_ser_circular(cls, valor: str) -> str:
        normalizada = valor.casefold()
        for proibida in FONTES_PROIBIDAS:
            if proibida in normalizada:
                raise ValueError(
                    f"fonte_referencia {valor!r} deriva da tabela de porções do "
                    "próprio projeto — a métrica mediria a tabela contra si mesma"
                )
        return valor

    @field_validator("fonte_url")
    @classmethod
    def _fonte_url_precisa_ser_localizavel(cls, valor: str) -> str:
        if not re.match(r"^(https?|isbn):", valor.strip(), flags=re.IGNORECASE):
            raise ValueError(
                f"fonte_url {valor!r} não é localizável — use uma URL http(s) ou "
                "um identificador `isbn:` para fonte impressa"
            )
        return valor

    @model_validator(mode="after")
    def _foto_exige_imagem(self) -> CasoEval:
        if self.estrato is Estrato.FOTO and not self.imagem_path:
            raise ValueError("caso do estrato 'foto' precisa de `imagem_path`")
        return self


def carregar_casos(caminho: Path | None = None) -> list[CasoEval]:
    """Lê o dataset JSONL, validando cada linha e recusando `id` duplicado."""
    destino = caminho or CASOS_PATH
    casos: list[CasoEval] = []
    vistos: set[str] = set()
    for numero, linha in enumerate(
        destino.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not linha.strip() or linha.lstrip().startswith("//"):
            continue
        try:
            caso = CasoEval.model_validate_json(linha)
        except Exception as exc:
            raise ValueError(f"{destino.name}:{numero} — caso inválido: {exc}") from exc
        if caso.id in vistos:
            raise ValueError(f"{destino.name}:{numero} — id duplicado: {caso.id!r}")
        vistos.add(caso.id)
        casos.append(caso)
    return casos


def sha_do_dataset(casos: list[CasoEval]) -> str:
    """Identidade do conjunto, para amarrar uma métrica ao dataset que a gerou.

    Calculado sobre o conteúdo canônico e ordenado por `id`, e não sobre os
    bytes do arquivo: reordenar linhas ou reformatar o JSON não muda o que foi
    medido, então não pode mudar a identidade.
    """
    canonico = json.dumps(
        [c.model_dump(mode="json") for c in sorted(casos, key=lambda c: c.id)],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def distribuicao_por_estrato(casos: list[CasoEval]) -> dict[str, int]:
    return {
        estrato.value: sum(1 for c in casos if c.estrato is estrato)
        for estrato in Estrato
    }
