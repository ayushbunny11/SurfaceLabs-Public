from __future__ import annotations

import os
import shutil
from typing import Optional, Dict
from uuid import uuid4
from pathlib import Path

from app.services.github.parser import extract_github_info
from app.utils.logget_setup import app_logger
from app.core.configs.app_config import REPO_STORAGE, system_config
import re

try:
    from git import Repo, GitCommandError
except Exception:
    Repo = None
    GitCommandError = Exception

_USER_ID_RE = r"^[A-Za-z0-9_.-]+$"


def clone_and_store(repo_url: str, user_id: str, depth: int = 1) -> Optional[Dict[str, str]]:
    """Clone `repo_url` into `REPO_STORAGE/{user_id}/{unique_id}`.

    Uses the module-level `REPO_STORAGE` path as the canonical repo storage
    location. Returns a dict with `user_id`, `unique_id`, and `path` on
    success, otherwise returns ``None``.
    """

    if not repo_url or not isinstance(repo_url, str):
        app_logger.debug("Invalid repo_url provided: %r", repo_url)
        return None

    if not user_id or not isinstance(user_id, str) or not re.match(_USER_ID_RE, user_id):
        app_logger.debug("Invalid user_id provided: %r", user_id)
        return None

    # Validate URL via parser first (quick sanity check)
    parsed = extract_github_info(repo_url)
    if parsed is None:
        app_logger.debug("Repo URL failed basic parsing: %s", repo_url)
        return None

    unique_id = uuid4().hex
    dest_dir = str(REPO_STORAGE / user_id / unique_id)

    try:
        Path(dest_dir).mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        app_logger.warning("Destination already exists, generating new id: %s", dest_dir)
        unique_id = uuid4().hex
        dest_dir = str(REPO_STORAGE / user_id / unique_id)
        Path(dest_dir).mkdir(parents=True, exist_ok=False)
    except Exception:
        app_logger.exception("Failed to create destination directory: %s", dest_dir)
        return None

    if Repo is None:
        app_logger.error("GitPython is not installed; cannot clone repository")
        try:
            shutil.rmtree(dest_dir)
        except Exception:
            app_logger.debug("Failed to remove dest dir after missing dependency: %s", dest_dir)
        return None

    try:
        clone_args = {"to_path": dest_dir}
        if depth is not None:
            Repo.clone_from(repo_url, dest_dir, depth=depth)
        else:
            Repo.clone_from(repo_url, dest_dir)

        app_logger.info("Cloned %s -> %s", repo_url, dest_dir)
        return {"user_id": user_id, "unique_id": unique_id, "path": dest_dir}

    except GitCommandError:
        app_logger.exception("Git clone failed for %s", repo_url)
        try:
            shutil.rmtree(dest_dir)
        except Exception:
            app_logger.debug("Failed to clean up after failed clone: %s", dest_dir)
        return None
    except Exception:
        app_logger.exception("Unexpected error during clone for %s", repo_url)
        try:
            shutil.rmtree(dest_dir)
        except Exception:
            app_logger.debug("Failed to clean up after unexpected clone error: %s", dest_dir)
        return None
