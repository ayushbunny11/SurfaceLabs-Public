from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints.feature_apis import parse_github

api_router = APIRouter(prefix="/v1")
api_router.include_router(health.router, prefix="/system", tags=["system"])
api_router.include_router(parse_github.router, prefix="/features", tags=["Functionality"])
