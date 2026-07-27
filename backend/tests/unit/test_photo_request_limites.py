"""Limites do payload da análise por foto.

`image_base64` era `str` sem teto. O corpo da requisição, a string base64 e os
bytes decodificados coexistem em memória, então um payload grande multiplica o
consumo por requisição — barato de enviar, caro de absorver.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.ai import MAX_IMAGE_BASE64_CHARS, PhotoAnalysisRequest


class TestTamanhoDaImagem:
    def test_imagem_de_tamanho_normal_e_aceita(self) -> None:
        req = PhotoAnalysisRequest(image_base64="A" * 100_000)
        assert req.mime_type == "image/jpeg"

    def test_imagem_acima_do_teto_e_recusada(self) -> None:
        with pytest.raises(ValidationError):
            PhotoAnalysisRequest(image_base64="A" * (MAX_IMAGE_BASE64_CHARS + 1))

    def test_imagem_vazia_e_recusada(self) -> None:
        with pytest.raises(ValidationError):
            PhotoAnalysisRequest(image_base64="")

    def test_teto_comporta_foto_de_celular(self) -> None:
        """~8 MB de base64 ≈ 6 MB de imagem — folgado para foto comprimida."""
        assert MAX_IMAGE_BASE64_CHARS >= 4 * 1024 * 1024


class TestMimeType:
    @pytest.mark.parametrize(
        "mime", ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    )
    def test_tipos_de_imagem_aceitos(self, mime: str) -> None:
        req = PhotoAnalysisRequest(image_base64="A" * 10, mime_type=mime)  # type: ignore[arg-type]
        assert req.mime_type == mime

    @pytest.mark.parametrize(
        "mime", ["text/html", "application/pdf", "image/svg+xml", "../../etc/passwd"]
    )
    def test_tipo_fora_do_vocabulario_e_recusado(self, mime: str) -> None:
        """O valor ia direto para a data URL enviada ao modelo."""
        with pytest.raises(ValidationError):
            PhotoAnalysisRequest(image_base64="A" * 10, mime_type=mime)  # type: ignore[arg-type]
