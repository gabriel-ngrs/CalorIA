"""Série temporal versionada do eval e o relatório derivado dela.

`runs/history.jsonl` é **append-only**: cada execução completa vira uma linha
que amarra a métrica ao commit, à versão e ao `sha` de cada prompt, ao modelo,
aos parâmetros de amostragem e ao `sha` do dataset. Sem essa amarração, uma
métrica isolada não diz de onde veio — e o "melhorou?" volta a ser opinião.

Uso, dentro do container backend::

    python -m evals.report registrar --relatorio r.json --git-commit <sha>
    python -m evals.report serie          # MdAPE ao longo dos commits
    python -m evals.report verificar --relatorio r.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

RUNS_DIR = Path(__file__).parent / "runs"
HISTORY_PATH = RUNS_DIR / "history.jsonl"

#: Limiares do gate da execução agendada. Espelham os já travados em
#: `tests/integration/test_golden_set.py` (NFR-6) — não são mais frouxos.
MDAPE_MAXIMO = 25.0
FRACAO_MINIMA_DENTRO_DE_10PCT = 0.50


class GateDoEvalError(RuntimeError):
    """Um limiar foi rompido, ou a execução terminou com caso vazio."""


def _git_commit_atual() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "desconhecido"


def montar_linha(
    relatorio: dict[str, Any],
    *,
    git_commit: str | None = None,
    invariancia: dict[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Monta a linha do histórico a partir de um relatório do runner."""
    commit = git_commit or _git_commit_atual()
    dataset = relatorio["dataset"]
    agregado = relatorio["agregado"]
    return {
        # `run_id` derivado do commit + `sha` do dataset: duas execuções do
        # mesmo commit sobre o mesmo dataset são a mesma medição (NFR-5).
        "run_id": run_id or f"{commit[:12]}-{dataset['sha'][:12]}",
        "git_commit": commit,
        "modelo": relatorio["modelo"],
        "amostragem": relatorio["amostragem"],
        "prompts": relatorio["prompts"],
        "dataset_sha": dataset["sha"],
        "dataset_n": dataset["n"],
        "dataset_distribuicao": dataset["distribuicao"],
        "casos_nao_verificados": dataset["casos_nao_verificados"],
        "agregado": agregado,
        "por_estrato": relatorio["por_estrato"],
        "falhas": relatorio.get("falhas", []),
        "invariancia": (invariancia or {}).get("resumo"),
    }


def registrar(linha: dict[str, Any], *, caminho: Path | None = None) -> Path:
    """Acrescenta uma linha ao histórico. Nunca reescreve linha existente."""
    destino = caminho or HISTORY_PATH
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(linha, ensure_ascii=False, sort_keys=True) + "\n")
    return destino


def carregar_historico(caminho: Path | None = None) -> list[dict[str, Any]]:
    destino = caminho or HISTORY_PATH
    if not destino.is_file():
        return []
    return [
        json.loads(linha)
        for linha in destino.read_text(encoding="utf-8").splitlines()
        if linha.strip()
    ]


def verificar(relatorio: dict[str, Any]) -> None:
    """Gate da execução agendada. Estoura quando algo regride.

    Sem `continue-on-error` no workflow: se esta função levanta, o job falha.
    """
    problemas: list[str] = []

    if relatorio.get("falhas"):
        # NFR-3: nenhuma execução pode terminar com casos vazios.
        ids = ", ".join(f["id"] for f in relatorio["falhas"])
        problemas.append(f"{len(relatorio['falhas'])} caso(s) sem resultado: {ids}")

    agregado = relatorio["agregado"]
    if not agregado["n"]:
        problemas.append("nenhum caso produziu métrica — execução vazia")
    else:
        if agregado["mdape"] > MDAPE_MAXIMO:
            problemas.append(
                f"MdAPE {agregado['mdape']:.2f}% acima do teto {MDAPE_MAXIMO:.2f}%"
            )
        dentro = agregado["dentro_da_tolerancia_kcal"]
        if dentro < FRACAO_MINIMA_DENTRO_DE_10PCT:
            problemas.append(
                f"apenas {dentro:.0%} dentro de ±10%, piso "
                f"{FRACAO_MINIMA_DENTRO_DE_10PCT:.0%}"
            )

    if problemas:
        raise GateDoEvalError("; ".join(problemas))


def serie_temporal(historico: list[dict[str, Any]]) -> str:
    """MdAPE ao longo dos commits, anotado com a versão de prompt vigente.

    Gerado só a partir do histórico — sem banco, sem rede, sem serviço externo.
    """
    if not historico:
        return "histórico vazio — nenhuma execução completa registrada ainda."

    linhas = [
        "SÉRIE TEMPORAL DO EVAL",
        "=" * 78,
        f"{'commit':<14} {'n':>3} {'MdAPE':>8} {'SSPB':>8} {'<=10%':>7}  prompts",
        "-" * 78,
    ]
    anterior: str | None = None
    for registro in historico:
        agregado = registro["agregado"]
        prompts = " ".join(
            f"{nome}@v{dados['versao']}"
            for nome, dados in sorted(registro["prompts"].items())
        )
        marca = "  ← versão de prompt mudou" if anterior and prompts != anterior else ""
        anterior = prompts
        if not agregado["n"]:
            linhas.append(f"{registro['git_commit'][:12]:<14} {0:>3}   (vazio)")
            continue
        linhas.append(
            f"{registro['git_commit'][:12]:<14} {agregado['n']:>3} "
            f"{agregado['mdape']:>7.2f}% {agregado['sspb']:>7.2f}% "
            f"{agregado['dentro_da_tolerancia_kcal']:>6.0%}  {prompts}{marca}"
        )
    return "\n".join(linhas)


def _carregar_json(caminho: str | None) -> dict[str, Any] | None:
    if not caminho:
        return None
    dados: dict[str, Any] = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return dados


def main() -> None:
    parser = argparse.ArgumentParser(description="Histórico e relatório do eval")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_registrar = sub.add_parser(
        "registrar", help="acrescenta uma execução ao histórico"
    )
    p_registrar.add_argument("--relatorio", required=True)
    p_registrar.add_argument("--invariancia", default=None)
    p_registrar.add_argument("--git-commit", default=None)

    sub.add_parser("serie", help="imprime a série temporal a partir do histórico")

    p_verificar = sub.add_parser("verificar", help="aplica o gate de limiares")
    p_verificar.add_argument("--relatorio", required=True)

    args = parser.parse_args()

    if args.comando == "registrar":
        relatorio = _carregar_json(args.relatorio)
        assert relatorio is not None
        linha = montar_linha(
            relatorio,
            git_commit=args.git_commit,
            invariancia=_carregar_json(args.invariancia),
        )
        print(f"registrado em {registrar(linha)}: run_id={linha['run_id']}")
    elif args.comando == "serie":
        print(serie_temporal(carregar_historico()))
    else:
        relatorio = _carregar_json(args.relatorio)
        assert relatorio is not None
        try:
            verificar(relatorio)
        except GateDoEvalError as exc:
            print(f"GATE DO EVAL REPROVADO: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        print("gate do eval aprovado")


if __name__ == "__main__":
    main()
