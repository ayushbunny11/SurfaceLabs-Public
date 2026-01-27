"""
Rate Limiting Configuration for SurfaceLabs API

Provides IP-based rate limiting using slowapi to protect against abuse.
Limits are per-day per-IP and stored in-memory (reset on server restart).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.configs.app_config import system_config
from app.utils.logget_setup import app_logger


# Rate limit configurations (per day per IP)
RATE_LIMIT_CONFIG = system_config.get("RATE_LIMITS")
RATE_LIMITS = {
    "clone": RATE_LIMIT_CONFIG.get("CLONE_LIMIT"),      # GitHub repo cloning
    "analysis": RATE_LIMIT_CONFIG.get("ANALYSIS_LIMIT"),   # LLM-based repository analysis
    "chat": RATE_LIMIT_CONFIG.get("CHAT_LIMIT"),      # Chat with AI agent
    "search": RATE_LIMIT_CONFIG.get("SEARCH_LIMIT"),   # Semantic search
    "explorer": RATE_LIMIT_CONFIG.get("EXPLORER_LIMIT"), # File tree and content
}


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    Handles proxied requests via X-Forwarded-For header.
    """
    # Check for forwarded header (when behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain (original client)
        client_ip = forwarded.split(",")[0].strip()
        app_logger.debug(f"[RATE_LIMIT] Client IP from X-Forwarded-For: {client_ip}")
        return client_ip
    
    # Fall back to direct client IP
    client_ip = get_remote_address(request)
    app_logger.debug(f"[RATE_LIMIT] Client IP from direct connection: {client_ip}")
    return client_ip


# Initialize the rate limiter with custom key function
limiter = Limiter(key_func=get_client_ip)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.
    Returns a user-friendly JSON response.
    """
    client_ip = get_client_ip(request)
    app_logger.warning(f"[RATE_LIMIT] Rate limit exceeded for IP: {client_ip}, endpoint: {request.url.path}")
    
    return JSONResponse(
        status_code=429,
        content={
            "status": "failure",
            "message": f"Rate limit exceeded. Please try again later. Limit: {exc.detail}",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "retry_after": str(exc.detail)
        }
    )


# Export limit strings for use in decorators
CLONE_LIMIT = RATE_LIMITS["clone"]
ANALYSIS_LIMIT = RATE_LIMITS["analysis"]
CHAT_LIMIT = RATE_LIMITS["chat"]
SEARCH_LIMIT = RATE_LIMITS["search"]
EXPLORER_LIMIT = RATE_LIMITS["explorer"]
