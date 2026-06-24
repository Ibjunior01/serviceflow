# app/repositories/__init__.py
from app.repositories.company import company_repo
from app.repositories.user import user_repo
from app.repositories.customer import customer_repo
from app.repositories.service_order import service_order_repo

__all__ = [
    "company_repo",
    "user_repo",
    "customer_repo",
    "service_order_repo",
]