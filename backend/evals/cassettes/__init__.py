"""Gravação e replay das respostas do provedor.

A camada rápida do eval roda a cada PR **sem tocar a rede**: cada chamada é
resolvida por uma gravação em disco, indexada pelo `sha256` do payload enviado.
O efeito é o que a spec pede — o teste falha se e somente se o **payload
mudar**, que é exatamente a regressão de prompt que se quer pegar de graça.

Gravar é opt-in por variável de ambiente. No CI a gravação fica desligada, então
um payload novo sem cassette correspondente **falha** em vez de sair chamando a
API silenciosamente.

Nenhuma chave de API entra num cassette: só o payload de mensagens e a resposta
de texto são gravados — nunca cabeçalhos, nunca o objeto de requisição.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

CASSETTES_DIR = Path(__file__).parent
#: Ligar para regravar contra o provedor real. Desligado no CI, por desenho.
VAR_GRAVACAO = "EVAL_RECORD_CASSETTES"


class CassetteAusenteError(RuntimeError):
    """Payload sem gravação correspondente e gravação desligada."""


def gravacao_ligada() -> bool:
    return os.getenv(VAR_GRAVACAO, "").lower() in {"1", "true", "yes"}


def chave_do_payload(payload: dict[str, Any]) -> str:
    """`sha256` da forma canônica do que seria enviado ao provedor.

    Ordena as chaves para que reformatar o dicionário não invalide a gravação;
    só uma mudança de **conteúdo** muda a chave.
    """
    canonico = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def caminho_do_cassette(chave: str, *, diretorio: Path | None = None) -> Path:
    return (diretorio or CASSETTES_DIR) / f"{chave}.json"


def gravar(
    payload: dict[str, Any], resposta: str, *, diretorio: Path | None = None
) -> Path:
    """Grava uma resposta. O payload é gravado junto, para diff legível no PR."""
    destino = caminho_do_cassette(chave_do_payload(payload), diretorio=diretorio)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(
            {"payload": payload, "resposta": resposta},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return destino


def reproduzir(payload: dict[str, Any], *, diretorio: Path | None = None) -> str:
    """Devolve a resposta gravada para este payload.

    Estoura quando não há gravação: é o sinal de que o payload mudou — prompt
    editado, parâmetro de amostragem alterado, contexto diferente.
    """
    chave = chave_do_payload(payload)
    arquivo = caminho_do_cassette(chave, diretorio=diretorio)
    if not arquivo.is_file():
        raise CassetteAusenteError(
            f"Sem cassette para o payload {chave[:16]}. O payload enviado ao "
            f"provedor mudou. Regrave com {VAR_GRAVACAO}=1 e revise o diff — "
            "se a mudança não era esperada, é regressão de prompt."
        )
    dados: dict[str, Any] = json.loads(arquivo.read_text(encoding="utf-8"))
    return str(dados["resposta"])
