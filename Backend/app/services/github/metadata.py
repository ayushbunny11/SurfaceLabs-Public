"""
GitHub Repository Metadata Fetcher
Fetches repository statistics from GitHub API (public repos only, no auth required)
"""
from typing import Optional, Dict, Any
from app.utils.logget_setup import app_logger
from app.utils import custom_request


# GitHub-specific headers
GITHUB_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}


async def fetch_repo_metadata(owner: str, repo: str) -> Optional[Dict[str, Any]]:
    """
    Fetch repository metadata from GitHub API.
    
    Args:
        owner: Repository owner (e.g., 'facebook')
        repo: Repository name (e.g., 'react')
    
    Returns:
        Dictionary with stars, forks, language, open_issues, default_branch, etc.
        Returns None if the request fails.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    
    response = await custom_request.get(url, headers=GITHUB_HEADERS)
    
    if response is None:
        return None
        
    if response.status_code == 200:
        data = response.json()
        app_logger.debug(f"Repository metadata: {data}")
        return {
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "language": data.get("language") or "Unknown",
            "default_branch": data.get("default_branch", "main"),
            "description": data.get("description", ""),
            "is_private": data.get("private", False),
            "size_kb": data.get("size", 0),
            "updated_at": data.get("updated_at"),
            "created_at": data.get("created_at"),
        }
    elif response.status_code == 404:
        app_logger.warning(f"Repository not found: {owner}/{repo}")
        return None
    elif response.status_code == 403:
        app_logger.warning("GitHub API rate limit exceeded")
        return None
    else:
        app_logger.error(f"GitHub API error: {response.status_code}")
        return None


async def fetch_branch_count(owner: str, repo: str) -> int:
    """
    Fetch the number of branches for a repository.
    Uses pagination to get accurate count for repos with many branches.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/branches"
    
    response = await custom_request.get(
        url, 
        headers=GITHUB_HEADERS,
        params={"per_page": 1}  # Just need count from Link header
    )
    
    if response is None:
        return 0
        
    if response.status_code == 200:
        # Check Link header for total count
        link_header = response.headers.get("Link", "")
        if 'rel="last"' in link_header:
            # Extract page number from last link
            import re
            match = re.search(r'page=(\d+)>; rel="last"', link_header)
            if match:
                return int(match.group(1))
        
        # If no pagination, count items directly
        branches = response.json()
        return len(branches)
    
    return 0
