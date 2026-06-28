from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routers.auth import router as auth_router
from .routers.beneficiary import router as beneficiary_router
from .routers.shopkeeper import router as shopkeeper_router
from .routers.officer import router as officer_router
from .routers.ai_routes import router as ai_router

app = FastAPI(
    title="Smart Ration Guardian API",
    description="AI-Powered Public Distribution Monitoring System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(beneficiary_router)
app.include_router(shopkeeper_router)
app.include_router(officer_router)
app.include_router(ai_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Smart Ration Guardian API"}


@app.get("/")
async def root():
    return {
        "status": "success",
        "data": {"service": "Smart Ration Guardian", "version": "1.0.0"},
        "message": "API is running",
    }
