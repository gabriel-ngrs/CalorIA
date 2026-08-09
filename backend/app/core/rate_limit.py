"""Rate limiting dos endpoints públicos e dos endpoints de IA.

Vive em `core/` — e não em `services/` — porque é infraestrutura de transporte
partilhada entre `main.py` (que registra o handler de 429) e os routers (que
decoram os endpoints). Um terceiro módulo evita o import circular entre eles.
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def _storage_uri() -> str | None:
    """`None` faz o `limits` usar contagem em memória do processo."""
    return settings.RATE_LIMIT_STORAGE_URI or None


def client_key(request: Request) -> str:
    """Identifica o cliente para efeito de contagem.

    Atrás do Caddy, `request.client.host` é o IP do proxy, e todos os usuários
    cairiam no mesmo balde — o limite viraria um teto global. Com o proxy à
    frente, o primeiro salto de `X-Forwarded-For` é o cliente real. Sem proxy o
    cabeçalho é forjável, e por isso a leitura é opcional e vem desligada.
    """
    if settings.RATE_LIMIT_TRUST_FORWARDED_FOR:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=client_key,
    storage_uri=_storage_uri(),
    enabled=settings.RATE_LIMIT_ENABLED,
    # Os cabeçalhos `X-RateLimit-*` do slowapi exigem um parâmetro
    # `response: Response` em cada endpoint decorado; os endpoints daqui
    # devolvem modelos Pydantic, e injetar `Response` só para o cabeçalho
    # poluiria seis assinaturas. O 429 continua explícito no corpo.
    headers_enabled=False,
    # Um Redis fora do ar não pode derrubar o login: sem o backend de contagem
    # o limite deixa de ser aplicado, como o cache de IA já degrada hoje.
    swallow_errors=True,
)
