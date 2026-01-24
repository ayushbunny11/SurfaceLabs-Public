from fastapi import APIRouter, Request

from app.core.rate_limiter import limiter, ANALYSIS_LIMIT

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/test-rate-limit")
@limiter.limit(ANALYSIS_LIMIT)
async def test_rate_limit(request: Request):
    """Test endpoint - 3 requests/minute limit. Hit 4+ times to see rate limit error."""
    return {
        "status": "ok",
        "message": "Rate limit not exceeded! Try again...",
        "limit": ANALYSIS_LIMIT
    }