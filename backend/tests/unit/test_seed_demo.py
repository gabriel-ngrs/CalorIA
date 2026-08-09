"""Conta de demonstração (fase E.3) — o que o escopo travado proíbe.

O escopo travado da fase nomeia três violações BLOQUEANTES: reusar senha pessoal
do owner, semear PII real, e dar à demo acesso a dado de outro usuário. As duas
primeiras são verificáveis aqui; a terceira é estrutural e está registrada no
`test_a_demo_nao_tem_privilegio` abaixo.

Zero banco e zero rede: o alvo é a declaração da conta, não a execução do seed.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]


def _carregar_seed():
    """Importa o script de seed, que vive fora de `app/` e não é um pacote."""
    caminho = RAIZ / "scripts" / "seed_dev_user.py"
    spec = importlib.util.spec_from_file_location("seed_dev_user", caminho)
    assert spec and spec.loader
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["seed_dev_user"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


seed = _carregar_seed()


class TestIdentidadeDaContaDemo:
    def test_a_demo_se_cria_sozinha_e_a_de_dev_nao(self) -> None:
        """A demo tem de ser semeável do zero; a de dev nunca é criada por script."""
        assert seed.CONTAS["demo"].criar_se_faltar is True
        assert seed.CONTAS["dev"].criar_se_faltar is False
        assert seed.CONTAS["dev"].senha is None

    def test_o_email_da_demo_nao_e_de_provedor_de_consumo(self) -> None:
        """PII real é violação BLOQUEANTE; um domínio próprio não é caixa de ninguém."""
        provedores = (
            "gmail",
            "hotmail",
            "outlook",
            "yahoo",
            "icloud",
            "proton",
            "live",
            "bol",
            "uol",
            "terra",
        )
        email = seed.CONTAS["demo"].email
        assert not any(f"@{p}." in email for p in provedores), email

    def test_a_senha_da_demo_e_sintetica_e_forte(self) -> None:
        senha = seed.SENHA_DEMO
        assert len(senha) >= 12
        assert re.search(r"[A-Z]", senha) and re.search(r"[a-z]", senha)
        assert re.search(r"\d", senha) and re.search(r"[^A-Za-z0-9]", senha)

    def test_a_senha_da_demo_nao_e_reusada_em_nenhuma_outra_conta(self) -> None:
        """A proibição literal do escopo travado, e o incidente que criou o Track A."""
        outras = [c.senha for k, c in seed.CONTAS.items() if k != "demo"]
        assert seed.SENHA_DEMO not in outras


README = RAIZ.parent / "README.md"

#: O container do backend monta só `backend/`, então o README da raiz não existe
#: lá dentro. Pular é honesto; fingir que passou seria pior, e deixar quebrar
#: local e verde no CI transformaria o guarda em ruído até alguém desligá-lo.
sem_readme = pytest.mark.skipif(
    not README.is_file(),
    reason="README.md da raiz não é alcançável daqui (container monta só backend/)",
)


@sem_readme
class TestCredenciaisPublicadas:
    """O README é a fonte que o AC-26 manda usar — ele não pode divergir do código."""

    @staticmethod
    def _readme() -> str:
        return README.read_text(encoding="utf-8")

    def test_o_readme_publica_exatamente_o_email_do_script(self) -> None:
        assert seed.CONTAS["demo"].email in self._readme()

    def test_o_readme_publica_exatamente_a_senha_do_script(self) -> None:
        # Se alguém trocar a senha no script e esquecer o README, o avaliador do
        # AC-26 não consegue entrar — e o defeito só apareceria na demo.
        assert seed.SENHA_DEMO in self._readme()

    def test_o_readme_declara_o_comando_de_reset(self) -> None:
        assert "make seed-demo" in self._readme()


class TestPrivilegio:
    def test_a_demo_nao_tem_privilegio(self) -> None:
        """Não há como dar privilégio: o modelo `User` não tem campo de papel.

        Se um `is_admin`/`role`/`is_superuser` for acrescentado um dia, este
        teste quebra — e é o momento certo de decidir o que a demo recebe, em vez
        de ela herdar o default do campo novo em silêncio.
        """
        from app.models.user import User

        colunas = set(User.__table__.columns.keys())
        assert not colunas & {"is_admin", "role", "is_superuser", "is_staff"}


@pytest.mark.parametrize("conta", ["dev", "demo"])
def test_toda_conta_declarada_tem_email_e_nome(conta: str) -> None:
    assert seed.CONTAS[conta].email and seed.CONTAS[conta].nome
