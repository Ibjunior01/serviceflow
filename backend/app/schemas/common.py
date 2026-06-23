"""
Schemas compartilhados — respostas genéricas reutilizáveis.
"""

from typing import Generic, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    """
    Schema base para todos os outros schemas.
    Configuração centralizada do Pydantic v2.
    """

    model_config = ConfigDict(
        from_attributes=True,      # Permite criar schema a partir de ORM objects
        populate_by_name=True,     # Aceita tanto alias quanto nome do campo
        str_strip_whitespace=True, # Remove espaços extras automaticamente
        use_enum_values=True,      # Serializa enums como seus valores (string)
    )


class MessageResponse(BaseSchema):
    """Resposta simples de mensagem — útil para DELETEs e ações."""

    message: str


class PaginatedResponse(BaseSchema, Generic[T]):
    """
    Wrapper de paginação genérico.

    Uso:
        PaginatedResponse[CustomerResponse]
        PaginatedResponse[ServiceOrderSummary]
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int