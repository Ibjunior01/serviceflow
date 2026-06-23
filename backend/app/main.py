from fastapi import FastAPI
from app.api.v1.endpoints.auth import router as auth_router
 
app = FastAPI(
    title="ServiceFlow API",
    description="Field Service Management para técnicos de refrigeração e ar-condicionado.",
    version="1.0.0",
)
 
# Routers
app.include_router(auth_router, prefix="/api/v1")
 
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}