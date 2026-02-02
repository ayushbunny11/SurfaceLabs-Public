from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.api.v1.endpoints.feature_apis import parse_github, analyze_repo, chat_apis, repo_explorer, proposals, download_repo

api_router = APIRouter(prefix="/v1")
api_router.include_router(health.router, prefix="/system", tags=["system"])
api_router.include_router(parse_github.router, prefix="/features", tags=["Github"])
api_router.include_router(analyze_repo.router, prefix="/features", tags=["Github"])
api_router.include_router(chat_apis.router, prefix="/features", tags=["Chat"])
api_router.include_router(repo_explorer.router, prefix="/features", tags=["Github"])
api_router.include_router(proposals.router, prefix="/features/proposals", tags=["Proposals"])
api_router.include_router(download_repo.router, prefix="/features", tags=["Download"])
