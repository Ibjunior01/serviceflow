from fastapi import FastAPI
from app.api.v1.endpoints.auth import router as auth_router
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    NotFoundError, ConflictError, ForbiddenError,
    BusinessRuleError, UnauthorizedError,
)
 
app = FastAPI(
    title="ServiceFlow API",
    description="Field Service Management para técnicos de refrigeração e ar-condicionado.",
    version="1.0.0",
)

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": exc.message})

@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": exc.message})

@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: Request, exc: ForbiddenError):
    return JSONResponse(status_code=403, content={"detail": exc.message})

@app.exception_handler(BusinessRuleError)
async def business_rule_handler(request: Request, exc: BusinessRuleError):
    return JSONResponse(status_code=422, content={"detail": exc.message})

@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request: Request, exc: UnauthorizedError):
    return JSONResponse(status_code=401, content={"detail": exc.message})
 
# Routers
app.include_router(auth_router, prefix="/api/v1")
 
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}