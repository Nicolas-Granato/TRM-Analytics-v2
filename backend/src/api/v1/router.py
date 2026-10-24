from fastapi import APIRouter
from src.api.v1.endpoints.audit import router as audit_router

api_router = APIRouter()

api_router.include_router(audit_router, prefix="/audit", tags=["Auditoria Fiscal"])
