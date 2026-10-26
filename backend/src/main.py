import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
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

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    req_id = str(uuid.uuid4())[:8]
    
    with logger.contextualize(request_id=req_id):
        start_time = time.perf_counter()
        logger.info("➡️ HTTP [{}] {}", request.method, request.url.path)
        
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            logger.info(
                "⬅️ HTTP [{}] {} | Status: {} | Tempo: {:.2f}s",
                request.method,
                request.url.path,
                response.status_code,
                duration
            )
            response.headers["X-Request-ID"] = req_id
            return response
        except Exception as exc:
            duration = time.perf_counter() - start_time
            logger.error(
                "❌ Falha HTTP [{}] {} | Erro: {} | Tempo: {:.2f}s",
                request.method,
                request.url.path,
                str(exc),
                duration
            )
            raise exc

Instrumentator().instrument(app).expose(app)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health Check"])
async def root():
    logger.info("Health check acessado")
    return {
        "status": "online",
        "app": "TRM Analytics v2",
        "message": "API rodando e pronta para processamento fiscal."
    }