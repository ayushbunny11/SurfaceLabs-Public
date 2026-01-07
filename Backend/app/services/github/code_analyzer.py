from __future__ import annotations
import os
import hashlib
import uuid
from typing import List, Set, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel
from app.schemas.feature_api_schemas import FileInfo
from app.core.configs.app_config import helper_config, REPO_STORAGE
from app.utils.logget_setup import app_logger
from google.adk.agents import Agent
import json

# FILE INDEXER

# ---------- DEFAULT IGNORE ----------
DEFAULT_IGNORE = helper_config["default_ignore"]
BINARY_EXTS  = helper_config["binary_exts"]

# ---------- HELPERS ----------
def detect_language(ext: str) -> str:
    return {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".java": "java",
        ".go": "go",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".rs": "rust",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(ext.lower(), "unknown")


def hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def load_gitignore(repo_path: Path) -> Set[str]:
    gitignore = repo_path / ".gitignore"
    patterns: Set[str] = set()

    if not gitignore.exists():
        return patterns

    for line in gitignore.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.add(line)

    return patterns


def matches_ignore(path: Path, patterns: Set[str]) -> bool:
    """Very light pattern support: folder names + suffix matches."""
    name = path.name

    if name in patterns:
        return True

    for p in patterns:
        # *.log, *.map, etc
        if p.startswith("*") and name.endswith(p.replace("*", "")):
            return True

    return False


# ---------- MAIN FUNCTION ----------
def build_file_index(repo_path: str) -> List[FileInfo]:
    try:
        repo = Path(repo_path).resolve()

        gitignore_patterns = load_gitignore(repo)
        results: List[FileInfo] = []

        for root, dirs, files in os.walk(repo):

            # skip ignored directories first (fast)
            dirs[:] = [
                d for d in dirs
                if d not in DEFAULT_IGNORE and not matches_ignore(Path(d), gitignore_patterns)
            ]

            for filename in files:
                file_path = Path(root) / filename
                rel = file_path.relative_to(repo)

                # ignore binary-ish or ignored names
                if (
                    matches_ignore(file_path, gitignore_patterns)
                    or filename in DEFAULT_IGNORE
                    or file_path.suffix in BINARY_EXTS
                ):
                    continue

                try:
                    text = file_path.read_text(errors="ignore")
                except Exception:
                    continue

                info = FileInfo(
                    path=str(file_path),
                    relative_path=str(rel),
                    size=file_path.stat().st_size,
                    lines_of_code=len(text.splitlines()),
                    extension=file_path.suffix,
                    language=detect_language(file_path.suffix),
                    hash=hash_file(file_path),
                )

                results.append(info)

        return results
    except Exception as e:
        app_logger.exception("Error building file index: %s", e)
        return []
    
# CHUNK BUILDER

MAX_TOKENS_PER_CHUNK = 8000
MAX_FILES_PER_CHUNK = 10
MAX_LINES_PER_CHUNK = 700

def estimate_tokens(text: str) -> int:
    """
    Rough token estimator. Good enough for chunk sizing.
    """
    return max(1, int(len(text) / 4))   # ~4 chars per token avg

def split_raw_text(text: str, parent_rel: str, directory: str):
    chunks = []
    start = 0
    part = 1

    while start < len(text):
        end = start + MAX_TOKENS_PER_CHUNK
        piece = text[start:end]

        chunks.append({
            "chunk_id": f"chunk-{uuid.uuid4().hex[:8]}",
            "directory": directory or ".",
            "files": [parent_rel],
            "parent_file": parent_rel,
            "part": part,
            "token_estimate": estimate_tokens(piece)
        })

        start = end
        part += 1

    return chunks


def split_file_raw(path: Path, rel: str):
    text = path.read_text(errors="ignore")
    directory = str(Path(rel).parent)
    return split_raw_text(text, rel, directory)


def chunk_files(repo_path: str, files: List[FileInfo]):
    """
    Create chunks grouped by directory, respecting token and file limits.
    """

    chunks = []

    # group files by their directory
    grouped = {}
    repo_root = Path(repo_path)

    for f in files:
        directory = str(Path(f.relative_path).parent) or "."
        grouped.setdefault(directory, []).append(f)

    # build chunks per directory
    for directory, file_group in grouped.items():

        current_files = []
        current_tokens = 0

        for file in file_group:
            file_path = repo_root / file.relative_path

            # read file text
            try:
                text = file_path.read_text(errors="ignore")
            except Exception:
                continue

            est = estimate_tokens(text)
            
            if est > MAX_TOKENS_PER_CHUNK:
                split_chunks = split_file_raw(file_path, file.relative_path)
                chunks.extend(split_chunks)
                continue

            # if adding this file exceeds safe limits, finalize current chunk
            if (
                current_files
                and (current_tokens + est > MAX_TOKENS_PER_CHUNK
                     or len(current_files) >= MAX_FILES_PER_CHUNK)
            ):
                chunks.append(
                    {
                        "chunk_id": f"chunk-{uuid.uuid4().hex[:8]}",
                        "directory": directory,
                        "files": [f.relative_path for f in current_files],
                        "token_estimate": current_tokens,
                    }
                )

                current_files = []
                current_tokens = 0

            current_files.append(file)
            current_tokens += est

        # finalize remainder
        if current_files:
            chunks.append(
                {
                    "chunk_id": f"chunk-{uuid.uuid4().hex[:8]}",
                    "directory": directory,
                    "files": [f.relative_path for f in current_files],
                    "token_estimate": current_tokens,
                }
            )

    return chunks

def run_analysis(agent: Agent, session_id, user_id):
    try:
        # Initiate the agent and run analysis logic here
        app_logger.info(f"Running analysis for session: {session_id}, user: {user_id}")
        
    except Exception as e:
        app_logger.exception("Error running analysis: %s", e)
        return None

def read_chunk(chunk_id: str, session_id: str):
    try:
        user_id = "918262"
        chunk_file_path = Path(REPO_STORAGE) / str(user_id) / "chunks" / f"chunk_{session_id}.json"
        indexed_file_path = Path(REPO_STORAGE) / str(user_id) / "indexed_file" / f"file_index_{session_id}.json"
        
        # load chunk data
        if not chunk_file_path.exists():
            app_logger.error("Chunk file not found: %s", chunk_file_path)
            return {"status": "failed", "message": "Chunk file not found", "data": ""}

        try:
            chunk_data = json.loads(chunk_file_path.read_text(encoding="utf-8"))
        except Exception as e:
            app_logger.exception("Failed to read chunk file: %s", e)
            return {"status": "failed", "message": "Failed to load chunks!", "data": ""}

        # get the specific chunk
        app_logger.info(chunk_data)
        target = next((c for c in chunk_data if c.get("chunk_id") == chunk_id), None)
        
        if not target:
            return {"status": "failed", "message": f"Chunk ID: {chunk_id} not found", "data": ""}
        
        # load index map: relative → absolute
        indexed = json.loads(indexed_file_path.read_text(encoding="utf-8"))
        index_map = {e["relative_path"]: e["path"] for e in indexed}

        files_content = {}
        for rel in target.get("files", []):
            abs_path = index_map.get(rel)

            if not abs_path:
                app_logger.warning("File %s missing in index", rel)
                continue

            try:
                files_content[rel] = Path(abs_path).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                app_logger.exception("Failed to read %s", abs_path)

        return files_content
    except Exception as e:
        app_logger.exception(f"Error while reading chunk_{chunk_id}: {e}")
        return {"status": "failed", "message": "Failed to read chunks!", "data": ""}
    