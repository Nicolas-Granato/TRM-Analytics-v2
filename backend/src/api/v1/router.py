from fastapi import APIRouter
from src.api.v1.endpoints import audit, export

api_router = APIRouter()

api_router.include_router(audit.router, prefix="/audit", tags=["Auditoria Fiscal"])
api_router.include_router(export.router, prefix="/export", tags=["Exportação de Relatórios"])