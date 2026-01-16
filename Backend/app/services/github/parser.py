import re
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse, unquote
from app.utils.logget_setup import app_logger


@dataclass
class GitHubInfo:
    owner: str
    repo: str
    branch: Optional[str] = None
    path: Optional[str] = None
    host: str = "github.com"

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "owner": self.owner,
            "repo": self.repo,
            "branch": self.branch,
            "path": self.path,
            "host": self.host,
        }


# Valid GitHub username/repo pattern
_RE_VALID_NAME = re.compile(r'^[A-Za-z0-9_.-]+$')

# Common invalid inputs that should fail fast
_INVALID_PATTERNS = [
    r'^https?://(www\.)?google\.com',
    r'^https?://(www\.)?stackoverflow\.com',
    r'^https?://(www\.)?gitlab\.com',
    r'^https?://(www\.)?bitbucket\.org',
]


class ValidationError(Exception):
    """Custom exception for validation errors with user-friendly messages."""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)


def _clean_repo(name: str) -> str:
    """Remove .git suffix from repo name."""
    return name[:-4] if name.endswith('.git') else name


def _validate_owner_repo(owner: str, repo: str) -> Tuple[bool, str]:
    """Validate owner and repo names against GitHub naming rules."""
    if not owner:
        return False, "Repository owner is missing"
    if not repo:
        return False, "Repository name is missing"
    if len(owner) > 39:
        return False, "GitHub username cannot exceed 39 characters"
    if len(repo) > 100:
        return False, "Repository name is too long"
    if not _RE_VALID_NAME.match(owner):
        return False, f"Invalid owner name: '{owner}'. Only letters, numbers, hyphens, underscores, and periods are allowed."
    if not _RE_VALID_NAME.match(repo):
        return False, f"Invalid repository name: '{repo}'. Only letters, numbers, hyphens, underscores, and periods are allowed."
    if owner.startswith('-') or owner.endswith('-'):
        return False, "GitHub username cannot start or end with a hyphen"
    if repo.startswith('.') or repo.endswith('.'):
        return False, "Repository name cannot start or end with a period"
    return True, ""


def extract_github_info(url: str) -> Optional[dict]:
    """Parse a GitHub-related URL and return owner/repo/branch/path/host.

    Supported inputs (examples):
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/branch/path/to/dir
    - https://github.com/owner/repo/blob/branch/path/to/file.py
    - git@github.com:owner/repo.git
    - https://raw.githubusercontent.com/owner/repo/branch/path

    Returns a dict or None if the URL couldn't be parsed.
    """
    try:
        # Handle SSH form: git@host:owner/repo(.git)
        ssh_match = re.match(r'^git@(?P<host>[^:]+):(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$', url)
        if ssh_match:
            host = ssh_match.group('host')
            owner = ssh_match.group('owner')
            repo = _clean_repo(ssh_match.group('repo'))
            
            is_valid, error_msg = _validate_owner_repo(owner, repo)
            if not is_valid:
                app_logger.debug('SSH validation failed: %s', error_msg)
                return None
            
            info = GitHubInfo(owner=owner, repo=repo, host=host)
            return info.to_dict()

        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path or ''

        # Accept URLs without scheme like 'github.com/owner/repo'
        if not netloc and parsed.scheme == '':
            # try parsing as if it had a scheme
            parsed = urlparse('https://' + url)
            netloc = parsed.netloc.lower()
            path = parsed.path or ''

        # Validate that it's a GitHub-like domain
        if not any(domain in netloc for domain in ['github.com', 'githubusercontent.com']):
            app_logger.debug("Not a GitHub domain: %s", netloc)
            return None

        # raw.githubusercontent.com has structure /owner/repo/branch/path
        if 'raw.githubusercontent.com' in netloc:
            segments = [seg for seg in path.split('/') if seg]
            if len(segments) >= 3:
                owner, repo = segments[0], _clean_repo(segments[1])
                
                is_valid, error_msg = _validate_owner_repo(owner, repo)
                if not is_valid:
                    app_logger.debug('Raw URL validation failed: %s', error_msg)
                    return None
                
                branch = unquote(segments[2])
                file_path = '/'.join(unquote(s) for s in segments[3:]) or None
                return GitHubInfo(owner=owner, repo=repo, branch=branch, path=file_path, host=netloc).to_dict()

        # github.com and subdomains (enterprise) handling
        if 'github.com' in netloc:
            segments = [seg for seg in path.split('/') if seg]
            
            if len(segments) < 2:
                app_logger.debug("Not enough path segments for owner/repo: %s", path)
                return None
            
            owner, repo = segments[0], _clean_repo(segments[1])
            
            is_valid, error_msg = _validate_owner_repo(owner, repo)
            if not is_valid:
                app_logger.debug("GitHub URL validation failed: %s", error_msg)
                return None

            # default values
            branch = None
            file_path = None

            if len(segments) >= 4 and segments[2] in ('tree', 'blob'):
                # Note: branch names with slashes are ambiguous in URL without repo API
                branch = unquote(segments[3])
                if len(segments) > 4:
                    file_path = '/'.join(unquote(s) for s in segments[4:])

            return GitHubInfo(owner=owner, repo=repo, branch=branch, path=file_path, host=netloc).to_dict()

        # Fallback: try to extract owner/repo via regex for uncommon forms
        fallback = re.search(r'(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)(?:\.git)?$', url)
        if fallback:
            owner = fallback.group('owner')
            repo = _clean_repo(fallback.group('repo'))
            
            is_valid, error_msg = _validate_owner_repo(owner, repo)
            if not is_valid:
                app_logger.debug("Fallback validation failed: %s", error_msg)
                return None
            
            return GitHubInfo(owner=owner, repo=repo, host=netloc or 'github.com').to_dict()

        app_logger.debug('Unable to parse GitHub URL: %s', url)
        return None
        
    except Exception:
        app_logger.exception('Unexpected error while parsing GitHub URL: %s', url)
        return None


def extract_github_info_with_error(url: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    Parse a GitHub URL and return (result, error_message).
    
    Returns:
        (dict, None) on success
        (None, error_message) on failure with user-friendly error
    """
    # Basic input validation with specific error messages
    if not url:
        return None, "Please provide a GitHub URL"
    
    if not isinstance(url, str):
        return None, "Invalid input type"

    url = url.strip()
    
    if not url:
        return None, "Please provide a GitHub URL"

    if len(url) < 10:
        return None, "URL is too short. Please provide a valid GitHub URL like: https://github.com/owner/repo"

    # Check for non-GitHub URLs
    for pattern in _INVALID_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            return None, "This doesn't look like a GitHub URL. Please provide a URL like: https://github.com/owner/repo"

    # Check if it looks like a GitHub URL
    if not any(domain in url.lower() for domain in ['github.com', 'githubusercontent.com', 'git@']):
        return None, "Please provide a valid GitHub URL (e.g., https://github.com/owner/repo)"

    # Try to parse it
    result = extract_github_info(url)
    
    if result is None:
        return None, "Could not parse the GitHub URL. Please use format: https://github.com/owner/repo"
    
    return result, None