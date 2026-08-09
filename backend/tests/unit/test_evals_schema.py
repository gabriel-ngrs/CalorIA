"""Contrato do caso de avaliação (AC-12)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from evals.schema import (
    CasoEval,
    Estrato,
    carregar_casos,
    distribuicao_por_estrato,
    sha_do_dataset,
)

_CASO_MINIMO = {
    "id": "x",
    "estrato": "simples",
    "descricao": "100 g de arroz cozido",
    "referencia_kcal": 128.0,
    "fonte_referencia": "TACO 4a edicao",
    "fonte_url": "https://www.nepa.unicamp.br/taco/",
    "data_de_adicao": "2026-08-02",
}


def _caso(**overrides: object) -> CasoEval:
    return CasoEval.model_validate({**_CASO_MINIMO, **overrides})


class TestCamposObrigatorios:
    def test_caso_minimo_valida(self) -> None:
        assert _caso().id == "x"

    @pytest.mark.parametrize("campo", sorted(_CASO_MINIMO))
    def test_faltar_qualquer_obrigatorio_reprova(self, campo: str) -> None:
        dados = {k: v for k, v in _CASO_MINIMO.items() if k != campo}
        with pytest.raises(ValidationError):
            CasoEval.model_validate(dados)

    def test_campo_desconhecido_reprova(self) -> None:
        """`extra=forbid` impede que um typo de campo passe em silêncio."""
        with pytest.raises(ValidationError):
            _caso(referencia_kcals=100)

    def test_kcal_precisa_ser_positiva(self) -> None:
        with pytest.raises(ValidationError):
            _caso(referencia_kcal=0)

    def test_estrato_desconhecido_reprova(self) -> None:
        with pytest.raises(ValidationError):
            _caso(estrato="bebida")


class TestFonteProibida:
    @pytest.mark.parametrize(
        "fonte",
        [
            "tabela portions do projeto",
            "PORTIONS",
            "tabela de porções interna",
            "derivado da tabela de porcoes",
        ],
    )
    def test_fonte_derivada_de_portions_reprova(self, fonte: str) -> None:
        """A circularidade que `eval_golden_set.py:20-27` identificou."""
        with pytest.raises(ValidationError, match="circular|própria|proprio|projeto"):
            _caso(fonte_referencia=fonte)

    def test_fonte_externa_passa(self) -> None:
        assert _caso(fonte_referencia="IBGE POF 2011").fonte_referencia


class TestFonteUrl:
    def test_url_http_passa(self) -> None:
        assert _caso(fonte_url="http://exemplo.org/tabela").fonte_url

    def test_isbn_passa(self) -> None:
        """Fonte impressa é auditável por ISBN."""
        assert _caso(fonte_url="isbn:978-85-7029-000-0").fonte_url

    @pytest.mark.parametrize("valor", ["nepa.unicamp.br", "TACO", "ftp://x/y"])
    def test_url_nao_localizavel_reprova(self, valor: str) -> None:
        with pytest.raises(ValidationError, match="localizável"):
            _caso(fonte_url=valor)

    def test_sem_fonte_url_reprova(self) -> None:
        dados = {k: v for k, v in _CASO_MINIMO.items() if k != "fonte_url"}
        with pytest.raises(ValidationError):
            CasoEval.model_validate(dados)


class TestEstratoFoto:
    def test_foto_sem_imagem_reprova(self) -> None:
        with pytest.raises(ValidationError, match="imagem_path"):
            _caso(estrato="foto")

    def test_foto_com_imagem_passa(self) -> None:
        caso = _caso(estrato="foto", imagem_path="imagens/pf.jpg")
        assert caso.estrato is Estrato.FOTO


class TestCarregamentoDoArquivo:
    def test_dataset_versionado_valida_inteiro(self) -> None:
        casos = carregar_casos()
        assert casos, "o dataset-semente não pode estar vazio"

    def test_todo_caso_semente_declara_procedencia(self) -> None:
        for caso in carregar_casos():
            assert caso.fonte_referencia
            assert caso.fonte_url

    def test_todo_caso_foi_conferido_na_publicacao(self) -> None:
        """A C.3 não conferia números na publicação; a C.4 conferiu todos."""
        assert all(c.verificada for c in carregar_casos())

    def test_id_duplicado_reprova(self, tmp_path: Path) -> None:
        linha = CasoEval.model_validate(_CASO_MINIMO).model_dump_json()
        arquivo = tmp_path / "casos.jsonl"
        arquivo.write_text(f"{linha}\n{linha}\n", encoding="utf-8")
        with pytest.raises(ValueError, match="duplicado"):
            carregar_casos(arquivo)

    def test_comentarios_e_linhas_vazias_sao_ignorados(self, tmp_path: Path) -> None:
        linha = CasoEval.model_validate(_CASO_MINIMO).model_dump_json()
        arquivo = tmp_path / "casos.jsonl"
        arquivo.write_text(f"// nota\n\n{linha}\n", encoding="utf-8")
        assert len(carregar_casos(arquivo)) == 1

    def test_linha_invalida_aponta_o_numero_da_linha(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "casos.jsonl"
        arquivo.write_text('{"id":"so-isso"}\n', encoding="utf-8")
        with pytest.raises(ValueError, match="casos.jsonl:1"):
            carregar_casos(arquivo)


class TestIdentidadeDoDataset:
    def test_sha_e_estavel_para_o_mesmo_conteudo(self) -> None:
        assert sha_do_dataset(carregar_casos()) == sha_do_dataset(carregar_casos())

    def test_sha_ignora_a_ordem_das_linhas(self) -> None:
        casos = carregar_casos()
        assert sha_do_dataset(casos) == sha_do_dataset(list(reversed(casos)))

    def test_sha_muda_quando_um_valor_muda(self) -> None:
        casos = carregar_casos()
        alterado = [*casos[1:], casos[0].model_copy(update={"referencia_kcal": 999.0})]
        assert sha_do_dataset(casos) != sha_do_dataset(alterado)


class TestDistribuicao:
    def test_reporta_os_tres_estratos_mesmo_vazios(self, tmp_path: Path) -> None:
        """Um estrato vazio tem de aparecer como zero, não sumir do relatório."""
        arquivo = tmp_path / "casos.jsonl"
        arquivo.write_text(
            CasoEval.model_validate(_CASO_MINIMO).model_dump_json() + "\n",
            encoding="utf-8",
        )
        distribuicao = distribuicao_por_estrato(carregar_casos(arquivo))
        assert set(distribuicao) == {"simples", "composto", "foto"}
        assert distribuicao["foto"] == 0

    def test_dataset_versionado_cobre_os_tres_estratos(self) -> None:
        """Depois da C.4 nenhum estrato pode estar vazio (FR-C3)."""
        distribuicao = distribuicao_por_estrato(carregar_casos())
        assert all(quantidade > 0 for quantidade in distribuicao.values())
