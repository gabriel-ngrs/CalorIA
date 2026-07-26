"""Normalização determinística de porção: unidade caseira → gramas.

A conversão sai do prompt e passa a ser feita em código, contra a tabela
`portions`. Corrige o achado A do bug 001: hoje a IA inventa a quantidade em
gramas sem âncora, e a mesma refeição descrita de duas formas produz massas
diferentes ("1 pizza grande 8 fatias" → 800g de massa; "8 fatias pizza
calabresa" → 400g de massa).

Regra de ouro do módulo: **a IA diz "8 fatias"; quem converte para gramas é
aqui**. Quando não há regra aplicável, o resultado é marcado como não-ancorado
para que o pipeline sinalize baixa confiança em vez de aceitar em silêncio.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Vocabulário de unidades
# ---------------------------------------------------------------------------

#: Unidade canônica → grafias aceitas (já normalizadas: minúsculas, sem acento).
_ALIASES: dict[str, tuple[str, ...]] = {
    "g": ("g", "gr", "grama", "gramas", "grs"),
    "mg": ("mg", "miligrama", "miligramas"),
    "kg": ("kg", "quilo", "quilos", "kilo", "kilos", "quilograma", "quilogramas"),
    "ml": ("ml", "mililitro", "mililitros"),
    "l": ("l", "litro", "litros", "lt"),
    "unidade": (
        "unidade",
        "unidades",
        "un",
        "und",
        "uni",
        "u",
        "item",
        "itens",
        "inteiro",
        "inteira",
    ),
    "fatia": ("fatia", "fatias", "pedaco de pizza", "slice"),
    "pedaco": ("pedaco", "pedacos", "naco"),
    "prato": ("prato", "pratos", "prato raso", "prato cheio", "pratinho"),
    "marmita": ("marmita", "marmitas", "quentinha", "marmitex"),
    "concha": ("concha", "conchas"),
    "escumadeira": ("escumadeira", "escumadeiras"),
    "colher_sopa": (
        "colher de sopa",
        "colheres de sopa",
        "colher sopa",
        "colheres sopa",
        "col sopa",
        "cs",
        "colher",
        "colheres",
    ),
    "colher_cha": (
        "colher de cha",
        "colheres de cha",
        "colher cha",
        "colheres cha",
        "col cha",
        "cc",
    ),
    "ponta_faca": ("ponta de faca", "ponta faca"),
    "copo": ("copo", "copos"),
    "copo_americano": ("copo americano", "copos americanos", "copo de requeijao"),
    "xicara": ("xicara", "xicaras"),
    "xicara_cha": ("xicara de cha", "xicaras de cha"),
    "taca": ("taca", "tacas"),
    "dose": ("dose", "doses", "shot"),
    "lata": ("lata", "latas", "latinha", "latinhas"),
    "garrafa": ("garrafa", "garrafas", "garrafinha"),
    "pote": ("pote", "potes", "potinho"),
    "scoop": ("scoop", "scoops", "medida", "medidas", "cacamba"),
    "file": ("file", "files", "filezinho"),
    "bife": ("bife", "bifes"),
    "espeto": ("espeto", "espetos", "espetinho"),
    "barra": ("barra", "barras"),
    "quadradinho": ("quadradinho", "quadradinhos", "quadrado", "quadrados"),
    "porcao": ("porcao", "porcoes", "serving"),
}

#: grafia normalizada → unidade canônica (invertido de _ALIASES)
_UNIDADE_POR_ALIAS: dict[str, str] = {
    alias: canonica for canonica, aliases in _ALIASES.items() for alias in aliases
}

#: Unidades que já são massa/volume e não precisam da tabela `portions`.
_DIRETAS: dict[str, float] = {"g": 1.0, "mg": 0.001, "kg": 1000.0}
#: Volume → gramas por densidade de líquido aquoso. Aproximação declarada.
_VOLUME: dict[str, float] = {"ml": 1.0, "l": 1000.0}

#: Números por extenso e frações comuns em português.
_NUMEROS: dict[str, float] = {
    "um": 1,
    "uma": 1,
    "dois": 2,
    "duas": 2,
    "tres": 3,
    "quatro": 4,
    "cinco": 5,
    "seis": 6,
    "sete": 7,
    "oito": 8,
    "nove": 9,
    "dez": 10,
    "onze": 11,
    "doze": 12,
    "meia": 0.5,
    "meio": 0.5,
    "metade": 0.5,
    "um quarto": 0.25,
    "tres quartos": 0.75,
    "dois tercos": 0.667,
    "um terco": 0.333,
    "uma duzia": 12,
    "duzia": 12,
    "meia duzia": 6,
}


def normalizar_texto(s: str) -> str:
    """Minúsculas, sem acento, espaços colapsados."""
    nfkd = unicodedata.normalize("NFKD", s or "")
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento).lower().strip()


def canonizar_unidade(unidade: str) -> str | None:
    """Mapeia uma grafia livre de unidade para a forma canônica.

    Retorna None quando a grafia não é reconhecida — o chamador decide o que
    fazer, em vez de receber um palpite silencioso.
    """
    u = normalizar_texto(unidade)
    if not u:
        return None
    if u in _UNIDADE_POR_ALIAS:
        return _UNIDADE_POR_ALIAS[u]
    # Tolera plural/singular residual e sufixos ("fatia media", "copo cheio")
    u_sem_plural = u[:-1] if u.endswith("s") else u
    if u_sem_plural in _UNIDADE_POR_ALIAS:
        return _UNIDADE_POR_ALIAS[u_sem_plural]
    primeira = u.split(" ")[0]
    if primeira in _UNIDADE_POR_ALIAS:
        return _UNIDADE_POR_ALIAS[primeira]
    return None


def interpretar_quantidade(valor: object) -> float | None:
    """Converte quantidade vinda como número, fração ou extenso.

    Aceita 2, "2", "2,5", "1/2", "dois", "meia dúzia".
    """
    if isinstance(valor, int | float):
        return float(valor)
    if not isinstance(valor, str):
        return None

    t = normalizar_texto(valor)
    if not t:
        return None
    if t in _NUMEROS:
        return _NUMEROS[t]

    # fração "1/2"
    if m := re.fullmatch(r"(\d+)\s*/\s*(\d+)", t):
        denom = float(m.group(2))
        return float(m.group(1)) / denom if denom else None

    # número decimal com vírgula ou ponto, possivelmente seguido de texto
    if m := re.match(r"(\d+(?:[.,]\d+)?)", t):
        return float(m.group(1).replace(",", "."))

    # "meia duzia", "um quarto" — expressões de duas palavras
    for expressao, n in _NUMEROS.items():
        if " " in expressao and t.startswith(expressao):
            return n
    return None


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegraPorcao:
    """Uma linha da tabela `portions`, tipada."""

    term: str
    unit: str
    grams: float
    grams_min: float
    grams_max: float
    priority: int
    source: str


@dataclass(frozen=True)
class PorcaoNormalizada:
    """Quantidade convertida para gramas, com a origem da conversão declarada."""

    gramas: float
    quantidade_original: float
    unidade_original: str
    unidade_canonica: str | None
    #: "direta" (já era massa) | "volume" (densidade) | "tabela" (portions)
    #: | "sem_ancora" (nenhuma regra — a IA que estimou)
    origem: str
    #: False quando a conversão não teve âncora ou caiu fora da faixa plausível.
    ancorada: bool
    plausivel: bool
    faixa_gramas: tuple[float, float] | None = None
    detalhe: str = ""

    @property
    def confiavel(self) -> bool:
        return self.ancorada and self.plausivel


class PortionNormalizer:
    """Converte (alimento, quantidade, unidade) em gramas usando a tabela `portions`."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._cache: list[RegraPorcao] | None = None

    async def _regras(self) -> list[RegraPorcao]:
        """Carrega a tabela inteira uma vez por instância (são ~99 linhas)."""
        if self._cache is None:
            rows = await self.db.execute(
                text(
                    "SELECT term, unit, grams, grams_min, grams_max, priority, source "
                    "FROM portions"
                )
            )
            self._cache = [
                RegraPorcao(
                    term=r["term"],
                    unit=r["unit"],
                    grams=float(r["grams"]),
                    grams_min=float(r["grams_min"]),
                    grams_max=float(r["grams_max"]),
                    priority=int(r["priority"]),
                    source=r["source"],
                )
                for r in rows.mappings()
            ]
        return self._cache

    async def normalizar(
        self,
        food_name: str,
        quantity: object,
        unit: str,
    ) -> PorcaoNormalizada:
        """Converte para gramas. Nunca levanta: sinaliza pelo campo `ancorada`."""
        qtd = interpretar_quantidade(quantity)
        canonica = canonizar_unidade(unit)

        if qtd is None or qtd <= 0:
            return PorcaoNormalizada(
                gramas=0.0,
                quantidade_original=0.0,
                unidade_original=unit,
                unidade_canonica=canonica,
                origem="sem_ancora",
                ancorada=False,
                plausivel=False,
                detalhe=f"quantidade ininterpretável: {quantity!r}",
            )

        # 1) Já é massa — nada a converter.
        if canonica in _DIRETAS:
            gramas = qtd * _DIRETAS[canonica]
            return PorcaoNormalizada(
                gramas=round(gramas, 2),
                quantidade_original=qtd,
                unidade_original=unit,
                unidade_canonica=canonica,
                origem="direta",
                ancorada=True,
                plausivel=0 < gramas <= 5000,
                detalhe="unidade de massa",
            )

        # 2) Volume → massa por densidade (aproximação declarada).
        if canonica in _VOLUME:
            gramas = qtd * _VOLUME[canonica]
            return PorcaoNormalizada(
                gramas=round(gramas, 2),
                quantidade_original=qtd,
                unidade_original=unit,
                unidade_canonica=canonica,
                origem="volume",
                ancorada=True,
                plausivel=0 < gramas <= 5000,
                detalhe="densidade de líquido aquoso (~1 g/ml)",
            )

        # 3) Unidade caseira → tabela `portions`.
        if canonica is not None:
            regra = await self._melhor_regra(food_name, canonica)
            if regra is not None:
                g_unit = regra.grams
                gramas = qtd * g_unit
                faixa = (qtd * regra.grams_min, qtd * regra.grams_max)
                generica = not regra.term
                return PorcaoNormalizada(
                    gramas=round(gramas, 2),
                    quantidade_original=qtd,
                    unidade_original=unit,
                    unidade_canonica=canonica,
                    origem="tabela",
                    # Regra genérica converte, mas não conta como âncora forte:
                    # a faixa é larga demais para sustentar um número calórico.
                    ancorada=not generica,
                    plausivel=True,
                    faixa_gramas=faixa,
                    detalhe=(
                        f"{regra.term or '(genérica)'} · 1 {canonica} = {g_unit}g "
                        f"· {regra.source}"
                    ),
                )

        # 4) Sem regra: a quantidade fica como veio e o item é marcado.
        return PorcaoNormalizada(
            gramas=round(qtd, 2),
            quantidade_original=qtd,
            unidade_original=unit,
            unidade_canonica=canonica,
            origem="sem_ancora",
            ancorada=False,
            plausivel=False,
            detalhe=f"sem regra de porção para unidade {unit!r}",
        )

    async def _melhor_regra(self, food_name: str, unidade: str) -> RegraPorcao | None:
        """Regra de maior prioridade cujo `term` aparece no nome do alimento.

        Empate de prioridade é resolvido pelo `term` mais longo — assim
        "pao de forma" vence "pao" para a unidade "fatia".
        """
        nome = normalizar_texto(food_name)
        candidatas = [
            r
            for r in await self._regras()
            if r.unit == unidade and (not r.term or r.term in nome)
        ]
        if not candidatas:
            return None
        return max(candidatas, key=lambda r: (r.priority, len(r.term)))

    async def checar_plausibilidade(
        self, food_name: str, gramas: float, unidade_canonica: str | None
    ) -> bool:
        """A massa informada cabe na faixa plausível da porção caseira?

        Usado para detectar erro de porção que o sanity check calórico não pega
        (achado C do bug 001): quando a IA erra a quantidade, `db_kcal` e
        `kcal_estimate` erram juntos e a divergência não acusa nada.
        """
        if gramas <= 0:
            return False
        if unidade_canonica in _DIRETAS or unidade_canonica in _VOLUME:
            return gramas <= 5000
        # Sem unidade caseira declarada, compara contra a faixa da unidade
        # "porcao" do alimento, quando existir.
        regra = await self._melhor_regra(food_name, "porcao")
        if regra is None:
            return 0 < gramas <= 2000
        return regra.grams_min * 0.5 <= gramas <= regra.grams_max * 5
