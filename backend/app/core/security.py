"""
ServiceFlow — Utilitários de segurança.

Responsabilidades:
- Hash e verificação de senha (bcrypt via passlib)
- Criação e decodificação de JWT (access + refresh tokens)
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Retorna o hash bcrypt da senha em texto puro."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica se a senha em texto puro corresponde ao hash."""
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def _make_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: UUID, company_id: UUID, role: str) -> str:
    """
    Access token de curta duração.
    Payload carrega: sub (user_id), company_id, role, type=access.
    """
    return _make_token(
        {
            "sub": str(user_id),
            "company_id": str(company_id),
            "role": role,
            "type": "access",
        },
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: UUID) -> str:
    """
    Refresh token de longa duração.
    Payload mínimo: sub (user_id), type=refresh.
    Não carrega role/company — esses são relidos do banco ao renovar.
    """
    return _make_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decodifica e valida um JWT.
    Lança JWTError se inválido ou expirado.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])