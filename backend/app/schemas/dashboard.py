from pydantic import Field

from app.schemas.common import BaseSchema
from app.schemas.service_order import ServiceOrderSummary


class DashboardStatusCounts(BaseSchema):
    """
    Quantidade de ordens por status.
    """

    draft: int = Field(default=0, ge=0)
    scheduled: int = Field(default=0, ge=0)
    in_progress: int = Field(default=0, ge=0)
    completed: int = Field(default=0, ge=0)
    invoiced: int = Field(default=0, ge=0)
    cancelled: int = Field(default=0, ge=0)


class DashboardMonthlyPoint(BaseSchema):
    """
    Quantidade de ordens criadas em um determinado mês.
    """

    year: int = Field(ge=2000)
    month: int = Field(ge=1, le=12)
    count: int = Field(ge=0)


class DashboardSummary(BaseSchema):
    """
    Resumo operacional exibido no dashboard.
    """

    status_counts: DashboardStatusCounts
    monthly_orders: list[DashboardMonthlyPoint]
    recent_orders: list[ServiceOrderSummary]