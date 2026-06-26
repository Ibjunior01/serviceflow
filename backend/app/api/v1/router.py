from fastapi import APIRouter

from app.api.v1.endpoints import auth, companies, customers, service_orders, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(companies.router)
api_router.include_router(users.router)
api_router.include_router(customers.router)
api_router.include_router(service_orders.router)