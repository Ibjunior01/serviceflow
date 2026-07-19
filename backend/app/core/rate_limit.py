"""
ServiceFlow — Rate limiting (slowapi).
"""

from slowapi import Limiter
from starlette.requests import Request


def get_real_client_ip(request: Request) -> str:
    """
    Em produção (Render), a aplicação fica atrás de um proxy reverso —
    o IP de conexão direta (request.client.host) é do proxy interno,
    não do cliente real. O IP real vem em X-Forwarded-For.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # X-Forwarded-For pode ter uma cadeia "cliente, proxy1, proxy2" — o primeiro é o cliente real
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=get_real_client_ip)