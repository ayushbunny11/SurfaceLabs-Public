"""
Centralized HTTP Client Utility
Provides a shared httpx client for all external API calls
"""
import httpx
from typing import Optional, Dict, Any, Literal
from app.utils.logget_setup import app_logger

# Default headers for all requests
DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "SurfaceLabs-App/1.0"
}

# Shared client instance (created on first use)
_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    """Get or create the shared httpx client."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
    return _client


async def close_client():
    """Close the shared client (call on app shutdown)."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None


async def request(
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Any] = None,
    timeout: Optional[float] = None,
) -> Optional[httpx.Response]:
    """
    Make an HTTP request using the shared client.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Full URL to request
        headers: Additional headers (merged with defaults)
        params: Query parameters
        json: JSON body (for POST/PUT/PATCH)
        data: Form data (for POST/PUT/PATCH)
        timeout: Override default timeout (seconds)
    
    Returns:
        httpx.Response on success, None on error
    """
    client = get_client()
    
    # Merge headers with defaults
    merged_headers = {**DEFAULT_HEADERS}
    if headers:
        merged_headers.update(headers)
    
    try:
        response = await client.request(
            method=method,
            url=url,
            headers=merged_headers,
            params=params,
            json=json,
            data=data,
            timeout=timeout,
        )
        return response
        
    except httpx.TimeoutException:
        app_logger.error(f"Request timeout: {method} {url}")
        return None
    except httpx.ConnectError:
        app_logger.error(f"Connection error: {method} {url}")
        return None
    except Exception as e:
        app_logger.exception(f"Request failed: {method} {url} - {e}")
        return None


# Convenience methods
async def get(url: str, **kwargs) -> Optional[httpx.Response]:
    """Make a GET request."""
    return await request("GET", url, **kwargs)


async def post(url: str, **kwargs) -> Optional[httpx.Response]:
    """Make a POST request."""
    return await request("POST", url, **kwargs)


async def put(url: str, **kwargs) -> Optional[httpx.Response]:
    """Make a PUT request."""
    return await request("PUT", url, **kwargs)


async def delete(url: str, **kwargs) -> Optional[httpx.Response]:
    """Make a DELETE request."""
    return await request("DELETE", url, **kwargs)
