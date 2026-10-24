from fastapi import FastAPI
from src.api.v1.router import api_router

app = FastAPI(
    title="TRM Analytics API",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

app.include_router(api_router, prefix="/api/v1")
