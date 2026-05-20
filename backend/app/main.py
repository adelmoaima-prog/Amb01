from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.agendas import router as agendas_router, escalas_router
from app.api.absenteismo import router as absenteismo_router
from app.api.producao import router as producao_router
from app.api.capacidade import router as capacidade_router
from app.api.relatorios import router as relatorios_router
from app.api.recursos import router as recursos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="HUC Ambulatorial — Sistema de Inteligência de Gestão",
    version="1.0.0",
    description="Plataforma de inteligência para gestão ambulatorial do Hospital Universitário",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/v1")
app.include_router(dashboard_router, prefix="/v1")
app.include_router(agendas_router, prefix="/v1")
app.include_router(escalas_router, prefix="/v1")
app.include_router(absenteismo_router, prefix="/v1")
app.include_router(producao_router, prefix="/v1")
app.include_router(capacidade_router, prefix="/v1")
app.include_router(relatorios_router, prefix="/v1")
app.include_router(recursos_router, prefix="/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "HUC Ambulatorial API"}
