from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.api.v1.router import api_router

app = FastAPI(
    title="TRM Analytics API",
    description="Engine de Engenharia de Dados de Alta Performance para Validação e Auditoria Fiscal (XML vs SPED/Sintegra)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "online",
        "app": "TRM Analytics v2",
        "message": "API rodando e pronta para processamento fiscal."
    }