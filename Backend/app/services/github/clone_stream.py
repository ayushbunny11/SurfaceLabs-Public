"""
SSE Progress Streaming for Clone Operations
Provides real-time progress updates during git clone
"""
import asyncio
import subprocess
import re
import shutil
from pathlib import Path
from uuid import uuid4
from typing import AsyncGenerator, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from app.utils.logget_setup import app_logger
from app.core.configs.app_config import REPO_STORAGE
from app.services.github.parser import extract_github_info

_USER_ID_RE = r"^[A-Za-z0-9_.-]+$"
_executor = ThreadPoolExecutor(max_workers=4)


def _run_git_clone_sync(repo_url: str, dest_dir: str, depth: int) -> tuple:
    """
    Synchronous git clone with progress capture.
    Returns (success: bool, progress_lines: list, error_msg: str)
    """
    cmd = ["git", "clone", "--progress", f"--depth={depth}", repo_url, dest_dir]
    progress_lines = []
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Git writes progress to stderr
        for line in iter(process.stderr.readline, ''):
            if line:
                progress_lines.append(line.strip())
        
        process.wait()
        
        if process.returncode != 0:
            return False, progress_lines, f"Git clone failed with exit code {process.returncode}"
        
        return True, progress_lines, ""
        
    except Exception as e:
        return False, progress_lines, str(e)


async def clone_with_progress(
    repo_url: str, 
    user_id: str, 
    depth: int = 1
) -> AsyncGenerator[Dict, None]:
    """
    Clone repository with progress streaming via SSE.
    
    Yields progress events:
    - {"event": "progress", "stage": "...", "percent": 0-100, "message": "..."}
    - {"event": "complete", "data": {...clone_info...}}
    - {"event": "error", "message": "..."}
    """
    
    # Validate inputs
    if not repo_url or not isinstance(repo_url, str):
        yield {"event": "error", "message": "Invalid repository URL"}
        return
    
    if not user_id or not re.match(_USER_ID_RE, user_id):
        yield {"event": "error", "message": "Invalid user ID"}
        return
    
    parsed = extract_github_info(repo_url)
    if parsed is None:
        yield {"event": "error", "message": "Unable to parse GitHub URL"}
        return
    
    # Create destination directory
    unique_id = uuid4().hex
    dest_dir = REPO_STORAGE / user_id / unique_id
    
    try:
        dest_dir.mkdir(parents=True, exist_ok=False)
    except Exception as e:
        yield {"event": "error", "message": f"Failed to create directory: {e}"}
        return
    
    # Stage 1: Starting
    yield {"event": "progress", "stage": "starting", "percent": 5, "message": "Preparing to clone..."}
    await asyncio.sleep(0.1)
    
    # Stage 2: Cloning (run in thread pool for Windows compatibility)
    yield {"event": "progress", "stage": "cloning", "percent": 15, "message": "Cloning repository..."}
    
    try:
        loop = asyncio.get_event_loop()
        success, progress_lines, error_msg = await loop.run_in_executor(
            _executor,
            _run_git_clone_sync,
            repo_url,
            str(dest_dir),
            depth
        )
        
        if not success:
            yield {"event": "error", "message": error_msg[:200]}
            try:
                shutil.rmtree(dest_dir)
            except:
                pass
            return
        
        # Parse last progress line for final percentage
        final_percent = 90
        if progress_lines:
            for line in reversed(progress_lines):
                match = re.search(r'(\d+)%', line)
                if match:
                    final_percent = min(90, 15 + int(int(match.group(1)) * 0.75))
                    break
        
        yield {"event": "progress", "stage": "cloning", "percent": final_percent, "message": "Finishing clone..."}
        await asyncio.sleep(0.1)
        
        # Stage 3: Complete
        yield {"event": "progress", "stage": "complete", "percent": 100, "message": "Clone complete!"}
        
        clone_info = {
            "user_id": user_id,
            "unique_id": unique_id,
            "path": str(dest_dir)
        }
        
        app_logger.info("Cloned %s -> %s", repo_url, dest_dir)
        yield {"event": "complete", "data": clone_info}
        
    except Exception as e:
        app_logger.exception("Clone failed: %s", e)
        yield {"event": "error", "message": str(e)[:200]}
        try:
            shutil.rmtree(dest_dir)
        except:
            pass
