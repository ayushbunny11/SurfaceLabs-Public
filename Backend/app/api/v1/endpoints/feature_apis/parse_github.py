import json
from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.schemas.feature_api_schemas import ParseGithubUrl
from app.utils.logget_setup import app_logger
from app.services.github.parser import extract_github_info, extract_github_info_with_error
from app.services.github.clone import clone_and_store
from app.services.github.clone_stream import clone_with_progress
from app.services.github.metadata import fetch_repo_metadata, fetch_branch_count

router = APIRouter()


@router.post("/parse_github_url")
async def parse_github_url(request: Request, request_data: ParseGithubUrl):
    """Original endpoint - returns after clone completes (no streaming)."""
    try:
        user_id = "918262"
        url = request_data.github_repo
        
        # Use parser with error messages
        parsed, error_msg = extract_github_info_with_error(url)
        if not parsed:
            response = {
                "status": "failure",
                "message": error_msg or "Unable to parse provided GitHub URL",
                "data": [],
            }
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=response)

        # Fetch repository metadata from GitHub API
        owner = parsed.get("owner")
        repo = parsed.get("repo")
        metadata = await fetch_repo_metadata(owner, repo)
        branch_count = await fetch_branch_count(owner, repo)
        
        # Merge metadata into parsed data
        if metadata:
            parsed["stars"] = metadata.get("stars", 0)
            parsed["forks"] = metadata.get("forks", 0)
            parsed["language"] = metadata.get("language", "Unknown")
            parsed["description"] = metadata.get("description", "")
            parsed["is_private"] = metadata.get("is_private", False)
            parsed["updated_at"] = metadata.get("updated_at")
        
        parsed["branches"] = branch_count

        clone_info = clone_and_store(url, user_id)
        if clone_info is None:
            response = {
                "status": "failure",
                "message": "Failed to clone repository",
                "data": [],
            }
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response)

        response = {"status": "success", "message": "Parsed successfully", "data": parsed}
        if clone_info:
            response["clone"] = clone_info
        return JSONResponse(status_code=status.HTTP_200_OK, content=response)
    except Exception as e:
        app_logger.exception("Error while parsing URL: %s", e)
        response = {"status": "failure", "message": "Parsing Failed!", "data": []}
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response)


@router.post("/parse_github_url/stream")
async def parse_github_url_stream(request: Request, request_data: ParseGithubUrl):
    """
    SSE endpoint for parsing and cloning with progress streaming.
    
    Returns Server-Sent Events with progress updates:
    - event: progress, data: {"stage": "...", "percent": 0-100, "message": "..."}
    - event: metadata, data: {...repo metadata...}
    - event: complete, data: {...clone info...}
    - event: error, data: {"message": "..."}
    """
    user_id = "918262"
    url = request_data.github_repo
    
    async def generate_events():
        try:
            # Use parser with error messages for user-friendly feedback
            parsed, error_msg = extract_github_info_with_error(url)
            if not parsed:
                yield f"event: error\ndata: {json.dumps({'event': 'error', 'message': error_msg, 'code': 'INVALID_URL'})}\n\n"
                return
            
            yield f"event: progress\ndata: {json.dumps({'stage': 'metadata', 'percent': 5, 'message': 'Fetching repository info...'})}\n\n"
            
            owner = parsed.get("owner")
            repo = parsed.get("repo")
            
            try:
                metadata = await fetch_repo_metadata(owner, repo)
                branch_count = await fetch_branch_count(owner, repo)
            except Exception as meta_err:
                app_logger.error(f"Failed to fetch metadata: {meta_err}")
                yield f"event: error\ndata: {json.dumps({'event': 'error', 'message': 'Failed to fetch repository info. The repo may not exist or be private.', 'code': 'METADATA_FAILED'})}\n\n"
                return
            
            if metadata is None:
                yield f"event: error\ndata: {json.dumps({'event': 'error', 'message': f'Repository not found: {owner}/{repo}. Please check the URL.', 'code': 'REPO_NOT_FOUND'})}\n\n"
                return
            
            # Merge metadata
            parsed["stars"] = metadata.get("stars", 0)
            parsed["forks"] = metadata.get("forks", 0)
            parsed["language"] = metadata.get("language", "Unknown")
            parsed["description"] = metadata.get("description", "")
            parsed["is_private"] = metadata.get("is_private", False)
            parsed["updated_at"] = metadata.get("updated_at")
            parsed["branches"] = branch_count
            
            # Send metadata to frontend
            yield f"event: metadata\ndata: {json.dumps(parsed)}\n\n"
            
            # Stream clone progress
            async for progress_event in clone_with_progress(url, user_id):
                event_type = progress_event.get("event", "progress")
                yield f"event: {event_type}\ndata: {json.dumps(progress_event)}\n\n"
                
                if event_type == "error":
                    return
                    
        except Exception as e:
            app_logger.exception("SSE stream error: %s", e)
            yield f"event: error\ndata: {json.dumps({'event': 'error', 'message': 'An unexpected error occurred. Please try again.', 'code': 'INTERNAL_ERROR'})}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
