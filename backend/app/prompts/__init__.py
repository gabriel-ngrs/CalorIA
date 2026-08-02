"""Registry de prompts versionados.

Os prompts de produção eram literais dentro dos parsers, sem identidade: não
havia como dizer *qual* prompt produziu um resultado, nem como comparar duas
versões. Aqui cada prompt vira arquivo versionado com `sha256` do texto bruto —
o que permite amarrar métrica de eval a versão de prompt (Track C da spec 002).

Layout em disco::

    app/prompts/<nome>/v<N>.txt        # system prompt (obrigatório)
    app/prompts/<nome>/v<N>.user.txt   # template da user message (opcional)

O conteúdo é lido **verbatim**: espaço em branco de prompt é significativo, e
por isso `app/prompts/` está excluído dos hooks de whitespace do pre-commit.

Regra de imutabilidade: um arquivo de versão não é editado depois de ter uma
execução de eval associada — mudança gera versão nova, no mesmo contrato de uma
migration Alembic.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent
_VERSION_FILE = re.compile(r"^v(\d+)\.txt$")

#: Separador usado só para derivar um `sha256` único da versão a partir das duas
#: partes. Nunca é enviado ao provedor.
_SHA_SEPARATOR = "\x00"


@dataclass(frozen=True)
class PromptVersion:
    """Uma versão imutável de um prompt, com identidade verificável."""

    name: str
    version: int
    system: str
    user_template: str | None
    sha256: str

    @property
    def ref(self) -> str:
        """Identificador curto para log e para o registro de eval."""
        return f"{self.name}@v{self.version}"

    def render(self, **variables: object) -> str:
        """Renderiza a user message. O `sha256` é do template, não daqui."""
        if self.user_template is None:
            raise ValueError(f"{self.ref} não tem template de user message")
        return self.user_template.format(**variables)


class PromptNotFoundError(LookupError):
    """Prompt ou versão inexistente em `app/prompts/`."""


def _sha256(system: str, user_template: str | None) -> str:
    raw = system if user_template is None else system + _SHA_SEPARATOR + user_template
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class PromptRegistry:
    """Carrega e resolve prompts versionados a partir do disco."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or _PROMPTS_DIR

    def names(self) -> list[str]:
        return sorted(
            d.name
            for d in self._root.iterdir()
            if d.is_dir() and not d.name.startswith("_") and self._versions(d)
        )

    def versions(self, name: str) -> list[int]:
        """Versões disponíveis de um prompt, em ordem crescente."""
        directory = self._root / name
        if not directory.is_dir():
            raise PromptNotFoundError(f"Prompt desconhecido: {name!r}")
        return self._versions(directory)

    def get(self, name: str, version: int | None = None) -> PromptVersion:
        """Resolve um prompt. Sem `version`, devolve a maior disponível."""
        disponiveis = self.versions(name)
        if not disponiveis:
            raise PromptNotFoundError(f"Prompt {name!r} não tem nenhuma versão")
        alvo = disponiveis[-1] if version is None else version
        if alvo not in disponiveis:
            raise PromptNotFoundError(
                f"Prompt {name!r} não tem versão v{alvo} (disponíveis: {disponiveis})"
            )
        return self._load(name, alvo)

    def all_active(self) -> list[PromptVersion]:
        """Versão ativa (a maior) de cada prompt — usado pelo teste de `sha`."""
        return [self.get(name) for name in self.names()]

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------

    @staticmethod
    def _versions(directory: Path) -> list[int]:
        encontradas = [
            int(m.group(1))
            for arquivo in directory.iterdir()
            if (m := _VERSION_FILE.match(arquivo.name))
        ]
        return sorted(encontradas)

    def _load(self, name: str, version: int) -> PromptVersion:
        directory = self._root / name
        system = (directory / f"v{version}.txt").read_text(encoding="utf-8")
        user_path = directory / f"v{version}.user.txt"
        user_template = (
            user_path.read_text(encoding="utf-8") if user_path.is_file() else None
        )
        return PromptVersion(
            name=name,
            version=version,
            system=system,
            user_template=user_template,
            sha256=_sha256(system, user_template),
        )


@lru_cache(maxsize=1)
def _registry() -> PromptRegistry:
    return PromptRegistry()


def get_prompt(name: str, version: int | None = None) -> PromptVersion:
    """Atalho para o registry padrão, com cache de leitura por processo."""
    return _cached_prompt(name, version)


@lru_cache(maxsize=64)
def _cached_prompt(name: str, version: int | None) -> PromptVersion:
    return _registry().get(name, version)
