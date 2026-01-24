from __future__ import annotations
import os
import hashlib
import uuid
from typing import List, Set, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel
import json
import asyncio

from google.adk.agents import Agent, LoopAgent
from google.adk.sessions import BaseSessionService
from google.adk.runners import Runner
from google.adk.events import Event
from google.genai import types
from google.genai.errors import ServerError
import re

from app.schemas.feature_api_schemas import FileInfo
from app.core.configs.app_config import settings, helper_config, REPO_STORAGE, prompt_config
from app.utils.logget_setup import app_logger, ai_logger
from app.services.agents.agent_config import tool_registry, session_manager
from app.services.ai_search.search_service import gemini_search_engine

# FILE INDEXER

# ---------- DEFAULT IGNORE ----------
DEFAULT_IGNORE = helper_config["default_ignore"]
IGNORE_EXTS  = helper_config["ignore_extensions"]

REPO_ANALYSIS_PROMPT = prompt_config.get("REPO_ANALYSIS_PROMPT")

JSON_BLOCK_PATTERN = re.compile(
    r"```json\s*(\{.*?\})\s*```",
    re.DOTALL
)

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
                    or file_path.suffix in IGNORE_EXTS
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

async def run_analysis_stream(agent: Agent, folder_id, user_id, chunk_ids):
    """
    Async generator that yields SSE events during analysis.
    Uses asyncio.Queue to yield events immediately as chunks complete.
    """
    try:
        ai_logger.info(f"Running analysis for folder_id: {folder_id}, user: {user_id}")
        if not REPO_ANALYSIS_PROMPT:
            ai_logger.error("REPO_ANALYSIS_PROMPT not found!")
            yield {"event": "error", "message": "Prompt configuration missing"}
            return
        
        agent.instruction = REPO_ANALYSIS_PROMPT
        
        total_chunks = len(chunk_ids)
        yield {"event": "progress", "stage": "init", "percent": 0, "message": f"Starting analysis of {total_chunks} chunks..."}
        
        MAX_CONCURRENT = 5
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        event_queue = asyncio.Queue()
        failed_chunks = []
        completed_count = 0
        
        async def process_chunk(chunk_id: str, index: int):
            nonlocal completed_count
            async with semaphore:
                await event_queue.put({
                    "event": "progress", 
                    "stage": "analyzing", 
                    "chunk_id": chunk_id, 
                    "chunk_index": index, 
                    "total": total_chunks, 
                    "message": f"Analyzing chunk {index + 1}/{total_chunks}..."
                })
                
                success = await _analyze_chunk(agent, chunk_id, folder_id, user_id)
                completed_count += 1
                percent = int((completed_count / total_chunks) * 90) + 5
                
                if success:
                    await event_queue.put({
                        "event": "chunk_complete", 
                        "chunk_id": chunk_id, 
                        "chunk_index": index, 
                        "percent": percent, 
                        "message": f"✓ Completed chunk {index + 1}/{total_chunks}"
                    })
                else:
                    failed_chunks.append(chunk_id)
                    await event_queue.put({
                        "event": "chunk_failed", 
                        "chunk_id": chunk_id, 
                        "chunk_index": index, 
                        "percent": percent, 
                        "message": f"✗ Failed chunk {index + 1}/{total_chunks}"
                    })
        
        # Start all tasks
        tasks = [asyncio.create_task(process_chunk(cid, i)) for i, cid in enumerate(chunk_ids)]
        
        # Yield events from queue as they arrive
        pending_tasks = len(tasks)
        while pending_tasks > 0 or not event_queue.empty():
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                yield event
                if event["event"] in ("chunk_complete", "chunk_failed"):
                    pending_tasks -= 1
            except asyncio.TimeoutError:
                # Check if all tasks are done
                if all(t.done() for t in tasks) and event_queue.empty():
                    break
        
        # Wait for all tasks to complete (they should be done by now)
        await asyncio.gather(*tasks, return_exceptions=True)
        
        yield {"event": "progress", "stage": "indexing", "percent": 95, "message": "Saving search index..."}
        gemini_search_engine.save(folder_id)
        
        if failed_chunks:
            yield {"event": "complete", "status": "partial", "percent": 100, "message": f"Analysis completed with {len(failed_chunks)} failed chunks", "failed_chunks": failed_chunks}
        else:
            yield {"event": "complete", "status": "success", "percent": 100, "message": "Analysis completed successfully"}
        
        ai_logger.info("All chunks processed successfully")
    
    except Exception as e:
        ai_logger.exception("Error running analysis: %s", e)
        yield {"event": "error", "message": str(e)}


async def _analyze_chunk(agent: Agent, chunk_id: str, folder_id: str, user_id: str) -> bool:
    """
    Analyze a single chunk. Returns True on success, False on failure.
    """
    session_service: BaseSessionService | None = None
    session_id = str(uuid.uuid4())
    
    try:
        chunk_data = read_chunk(chunk_id, folder_id)
        
        user_content = types.Content(
            role="user",
            parts=[
                types.Part(text=f"Analyze this data: {json.dumps(chunk_data)}"),
                types.Part(text="Generate the output in the provided structure.")
            ]
        )
        
        ai_logger.debug(f"[{chunk_id}] Creating session {session_id}")
        await session_manager.create(APP_NAME=settings.APP_NAME, user_id=user_id, session_id=session_id)
        session_service = session_manager.get_service()
        
        runner = Runner(
            app_name=settings.APP_NAME,
            agent=agent,
            session_service=session_service,    
        )
    
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content,
        ):
            ai_logger.debug(f"[{chunk_id}] Event ID: {event.id}, Author: {event.author}")
            
            if event.content and event.content.parts:
                if event.get_function_calls():
                    ai_logger.debug(f"[{chunk_id}] Function Call!")
                    calls = event.get_function_calls()
                    if calls:
                        for call in calls:
                            ai_logger.debug(f"[{chunk_id}] [TOOL_CALL] Name: {call.name} Args: {call.args}")
                            
                if event.get_function_responses():
                    responses = event.get_function_responses()
                    for response in responses:
                        ai_logger.debug(f"[{chunk_id}] [TOOL_RESPONSE] Tool: {response.name}")
                        
            if event.actions and event.actions.state_delta:
                ai_logger.debug(f"[{chunk_id}] State changes: {event.actions.state_delta}")
            
            if event.actions and event.actions.artifact_delta:
                ai_logger.debug(f"[{chunk_id}] Artifacts saved: {event.actions.artifact_delta}")
            
            if event.is_final_response():
                ai_logger.debug(f"[{chunk_id}] Final response received")
                if event.content and event.content.parts and event.content.parts[0].text:
                    final_text = event.content.parts[0].text if not event.partial else ""
                    ai_logger.debug(f"[{chunk_id}] Agent response received")
                    
                    final_chunks = extract_chunk_summaries(final_text)
                    for final_chunk in final_chunks:
                        saved = save_chunk_to_session(user_id=user_id, folder_id=folder_id, chunk_summary=final_chunk)
                        if not saved:
                            ai_logger.error(f"[{chunk_id}] Failed to save chunk summary")
                            return False
                
                ai_logger.debug(f"[{chunk_id}] Session completed")
                return True

            if event.error_code or event.error_message:
                if event.error_message and ("RESOURCE_EXHAUSTED" in event.error_message):
                    ai_logger.warning(f"[{chunk_id}] Rate limited, sleeping 45s")
                    await asyncio.sleep(45)
                    ai_logger.debug(f"[{chunk_id}] Resuming after rate limit")
                    
                ai_logger.error(f"[{chunk_id}] Error: {event.error_code or ''} - {event.error_message or ''}")
        
        return True
        
    except ServerError as e:
        ai_logger.exception(f"[{chunk_id}] ServerError during analysis")
        ai_logger.error(f"[{chunk_id}] Status: {e.status}, Message: {e.message}, Code: {e.code}")
        return False
        
    except Exception as e:
        ai_logger.exception(f"[{chunk_id}] Error: {e}")
        return False
        
    finally:
        if session_service and session_id:
            try:
                await session_service.delete_session(
                    app_name=settings.APP_NAME, 
                    user_id=user_id, 
                    session_id=session_id
                )
                ai_logger.debug(f"[{chunk_id}] Session {session_id} deleted")
            except Exception as cleanup_error:
                ai_logger.error(f"[{chunk_id}] Failed to delete session: {cleanup_error}")

def read_chunk(chunk_id: str, session_id: str):
    """
    Load and return the text content for all files associated with a chunk
    within a given session.

    Args:
        chunk_id (str): Unique identifier of the chunk to read.
        session_id (str): Session identifier used to locate chunk and index data.

    Returns:
        dict:
            On success: { "<relative_path>": "<file_content>", ... }
            On failure: {
                "status": "failed",
                "message": "<error reason>",
                "data": ""
            }
    """
    try:
        user_id = "918262"
        chunk_file_path = Path(REPO_STORAGE) / str(user_id) / "chunks" / f"chunk_{session_id}.json"
        indexed_file_path = Path(REPO_STORAGE) / str(user_id) / "indexed_file" / f"file_index_{session_id}.json"
        
        # load chunk data
        if not chunk_file_path.exists():
            ai_logger.error("Chunk file not found: %s", chunk_file_path)
            return {"status": "failed", "message": "Chunk file not found", "data": ""}

        try:
            chunk_data = json.loads(chunk_file_path.read_text(encoding="utf-8"))
        except Exception as e:
            ai_logger.exception("Failed to read chunk file: %s", e)
            return {"status": "failed", "message": "Failed to load chunks!", "data": ""}

        # get the specific chunk
        # ai_logger.info(chunk_data)
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
                ai_logger.warning("File %s missing in index", rel)
                continue

            try:
                files_content[rel] = Path(abs_path).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                ai_logger.exception("Failed to read %s", abs_path)

        return files_content
    except Exception as e:
        ai_logger.exception(f"Error while reading chunk_{chunk_id}: {e}")
        return {"status": "failed", "message": "Failed to read chunks!", "data": ""}
    

def extract_chunk_summaries(llm_text: str) -> list[dict]:
    chunks = []

    matches = JSON_BLOCK_PATTERN.findall(llm_text)

    for raw_json in matches:
        try:
            chunks.append(json.loads(raw_json))
        except json.JSONDecodeError:
            continue

    return chunks

def save_chunk_to_session(
    user_id: str,
    folder_id: str,
    chunk_summary: dict,
):
    try:
        new_chunk_id = str(uuid.uuid4())
        session_path = (
            Path(REPO_STORAGE)
            / str(user_id)
            / "llm_response"
            / f"response_{folder_id}.json"
        )

        session_path.parent.mkdir(parents=True, exist_ok=True)

        if session_path.exists():
            data = json.loads(session_path.read_text(encoding="utf-8"))
        else:
            data = {
                "folder_id": folder_id,
                "schema_version": "1.0",
                "chunks": {},
                "files_index": {}
            }

        chunk_id = new_chunk_id

        # Save chunk
        data["chunks"][chunk_id] = chunk_summary

        faiss_id = gemini_search_engine.upload_document(chunk_id, json.dumps(chunk_summary))
        data["chunks"][chunk_id]["faiss_id"] = faiss_id
        
        # Update file → chunk index
        for file in chunk_summary.get("files", []):
            data["files_index"].setdefault(file, [])
            if chunk_id not in data["files_index"][file]:
                data["files_index"][file].append(chunk_id)
        
        session_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )
        return True
    except Exception as e:
        ai_logger.debug(f"Error occured while saving/reading the json file: {e}", )
        return False
