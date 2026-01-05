import os
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict
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


_RE_VALID_NAME = re.compile(r'^[A-Za-z0-9_.-]+$')


def _clean_repo(name: str) -> str:
    return name[:-4] if name.endswith('.git') else name


def extract_github_info(url: str) -> Optional[dict]:
    """Parse a GitHub-related URL and return owner/repo/branch/path/host.

    Supported inputs (examples):
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/branch/path/to/dir
    - https://github.com/owner/repo/blob/branch/path/to/file.py
    - git@github.com:owner/repo.git
    - https://raw.githubusercontent.com/owner/repo/branch/path

    Limitations:
    - When branch names contain slashes (e.g. feature/x), GitHub URLs may be
      ambiguous without repository API calls. This function treats the segment
      immediately following ``tree`` or ``blob`` as the branch and the remainder
      (if any) as the path.

    Returns a dict or ``None`` if the URL couldn't be parsed.
    """

    if not url or not isinstance(url, str):
        return None

    url = url.strip()

    try:
        # Handle SSH form: git@host:owner/repo(.git)
        ssh_match = re.match(r'^git@(?P<host>[^:]+):(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$', url)
        if ssh_match:
            host = ssh_match.group('host')
            owner = ssh_match.group('owner')
            repo = _clean_repo(ssh_match.group('repo'))
            if not (_RE_VALID_NAME.match(owner) and _RE_VALID_NAME.match(repo)):
                app_logger.debug('SSH parse produced invalid owner/repo: %s/%s', owner, repo)
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

        # raw.githubusercontent.com has structure /owner/repo/branch/path
        if 'raw.githubusercontent.com' in netloc:
            segments = [seg for seg in path.split('/') if seg]
            if len(segments) >= 3:
                owner, repo = segments[0], _clean_repo(segments[1])
                branch = unquote(segments[2])
                file_path = '/'.join(unquote(s) for s in segments[3:]) or None
                return GitHubInfo(owner=owner, repo=repo, branch=branch, path=file_path, host=netloc).to_dict()

        # github.com and subdomains (enterprise) handling
        if 'github.com' in netloc:
            segments = [seg for seg in path.split('/') if seg]
            if len(segments) >= 2:
                owner, repo = segments[0], _clean_repo(segments[1])
                if not (_RE_VALID_NAME.match(owner) and _RE_VALID_NAME.match(repo)):
                    app_logger.debug('Invalid owner or repo parsed: %s / %s', owner, repo)
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
            return GitHubInfo(owner=owner, repo=repo, host=netloc or 'github.com').to_dict()

        app_logger.debug('Unable to parse GitHub URL: %s', url)
        return None
    except Exception:
        app_logger.exception('Unexpected error while parsing GitHub URL: %s', url)
        return None
    w