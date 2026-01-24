from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path
import json
import uuid

from google.genai.errors import ServerError

from app.schemas.feature_api_schemas import *
from app.utils.logget_setup import app_logger
from app.core.configs.app_config import system_config, REPO_STORAGE, settings
from app.services.github.code_analyzer import build_file_index, chunk_files, run_analysis_stream
from app.services.agents.agent_config import agent_manager, memory_store, tool_registry, session_manager
from app.services.ai_search.search_service import gemini_search_engine
from app.core.rate_limiter import limiter, ANALYSIS_LIMIT, SEARCH_LIMIT

STATUS_SUCCESS = system_config.get("STATUS_SUCCESS", "success")
STATUS_FAILURE = system_config.get("STATUS_FAILURE", "failure")
app_logger.debug("API_KEY:")
app_logger.debug(settings.GOOGLE_API_KEY)

router = APIRouter()

@router.post("/analysis/stream")
@limiter.limit(ANALYSIS_LIMIT)
async def analyze_repo_stream(request: Request, request_data: AnalysisRequest):
    """SSE endpoint for analysis with real-time progress updates."""
    user_id = "918262"
    folder_ids = request_data.folder_ids[0]
    
    async def generate_events():
        try:
            file_path = str(REPO_STORAGE / f"{user_id}" / f"{folder_ids}")
            
            chunk_file_path = Path(REPO_STORAGE) / str(user_id) / "chunks" / f"chunk_{folder_ids}.json"
            chunk_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            indexed_file_path = Path(REPO_STORAGE) / str(user_id) / "indexed_file" / f"file_index_{folder_ids}.json"
            indexed_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            yield f"event: progress\ndata: {json.dumps({'stage': 'init', 'percent': 0, 'message': 'Creating analysis agent...'})}\n\n"
            
            analysis_agent = agent_manager.create(name="Analysis_Agent", model=settings.FLASH_MODEL, instruction="", description="Analysis Agent")
            
            yield f"event: progress\ndata: {json.dumps({'stage': 'indexing', 'percent': 2, 'message': 'Indexing repository files...'})}\n\n"
            
            indexed_file = build_file_index(file_path)
            if len(indexed_file) == 0:
                yield f"event: error\ndata: {json.dumps({'message': 'No files found for analysis.'})}\n\n"
                return
            
            yield f"event: progress\ndata: {json.dumps({'stage': 'chunking', 'percent': 5, 'message': f'Found {len(indexed_file)} files. Creating chunks...'})}\n\n"
            
            chunked_data = chunk_files(file_path, indexed_file)
            
            indexed_files = [
                f.model_dump(exclude_none=True, by_alias=True) if hasattr(f, "model_dump") else f
                for f in indexed_file
            ]
            
            chunk_file_path.write_text(json.dumps(chunked_data, indent=2), encoding="utf-8")
            indexed_file_path.write_text(json.dumps(indexed_files, indent=2), encoding="utf-8")
            
            chunked_ids = [chunk.get("chunk_id") for chunk in chunked_data]
            
            yield f"event: progress\ndata: {json.dumps({'stage': 'analyzing', 'percent': 5, 'message': f'Created {len(chunked_ids)} chunks. Starting analysis...'})}\n\n"
            
            async for event in run_analysis_stream(agent=analysis_agent, folder_id=folder_ids, user_id=user_id, chunk_ids=chunked_ids):
                yield f"event: {event.get('event', 'progress')}\ndata: {json.dumps(event)}\n\n"
                
                if event.get('event') == 'error':
                    return
        
        except Exception as e:
            app_logger.exception("SSE stream error: %s", e)
            yield f"event: error\ndata: {json.dumps({'message': 'An unexpected error occurred.'})}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/analysis")
@limiter.limit(ANALYSIS_LIMIT)
async def analyze_repo(request: Request, request_data: AnalysisRequest):
    """Non-streaming analysis endpoint (legacy)."""
    try:
        user_id = "918262"
        folder_ids = request_data.folder_ids[0]
        file_path = str(REPO_STORAGE / f"{user_id}" / f"{folder_ids}")
        
        chunk_file_path = Path(REPO_STORAGE) / str(user_id) / "chunks" / f"chunk_{folder_ids}.json"
        chunk_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        indexed_file_path = Path(REPO_STORAGE) / str(user_id) / "indexed_file" / f"file_index_{folder_ids}.json"
        indexed_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        analysis_agent = agent_manager.create(name="Analysis_Agent", model=settings.FLASH_MODEL, instruction="", description="Analysis Agent")
        
        indexed_file = build_file_index(file_path)
        if len(indexed_file) == 0:
            response = {"status": STATUS_FAILURE, "message": "No files found for analysis.", "data": []}
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)
        
        chunked_data = chunk_files(file_path, indexed_file)
        
        indexed_files = [
            f.model_dump(exclude_none=True, by_alias=True) if hasattr(f, "model_dump") else f
            for f in indexed_file
        ]
        
        chunk_file_path.write_text(json.dumps(chunked_data, indent=2), encoding="utf-8")
        indexed_file_path.write_text(json.dumps(indexed_files, indent=2), encoding="utf-8")
        
        chunked_ids = [chunk.get("chunk_id") for chunk in chunked_data]
        
        # Consume all events and check final status
        final_event = None
        async for event in run_analysis_stream(agent=analysis_agent, folder_id=folder_ids, user_id=user_id, chunk_ids=chunked_ids):
            final_event = event
        
        if final_event and final_event.get("event") == "error":
            response = {"status": STATUS_FAILURE, "message": final_event.get("message", "Analysis failed"), "data": []}
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response)
        
        response = {"status": STATUS_SUCCESS, "message": "Analysis Completed!", "data": []}
        return JSONResponse(status_code=status.HTTP_200_OK, content=response)
    
    except Exception as e:
        app_logger.exception("Error while analyzing repository: %s", e)
        response = {"status": STATUS_FAILURE, "message": "Analysis Failed! Please try again later!", "data": []}
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response)
    
@router.post("/q", response_model=SearchResponse)
@limiter.limit(SEARCH_LIMIT)
async def search_indexed_docs(request: Request, request_data: SearchRequest):
    """
    Search through indexed document chunks using semantic similarity.
    
    Args:
        request_data: SearchRequest containing query, folder_id, and top_k
        
    Returns:
        SearchResponse with matching document chunks and similarity scores
    """
    try:
        user_id = "918262"
        query = request_data.query.strip()
        
        app_logger.info(
            f"Search request - User: {user_id}, "
            f"Query: '{query[:50]}...'"
        )
        gemini_search_engine.load()
        
        if not gemini_search_engine:
            app_logger.error("Gemini search engine not initialized properly.")
            response = {
                "status": STATUS_FAILURE,
                "message": "Search service is currently unavailable. Please try again later.",
                "data": [],
                "total_results": 0,
                "query": query
            }
            return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=response)
        
        # Validate that index exists
        if gemini_search_engine.index.ntotal == 0:
            app_logger.warning(f"Search attempted on empty index. No documents indexed yet.")
            response = {
                "status": STATUS_SUCCESS,
                "message": "No documents indexed yet. Please analyze the repository first.",
                "data": [],
                "total_results": 0,
                "query": query
            }
            return JSONResponse(status_code=status.HTTP_200_OK, content=response)
        
        # Perform semantic search
        search_results = gemini_search_engine.search(query)
        
        if not search_results:
            app_logger.info(f"No results found for query: '{query}'")
            response = {
                "status": STATUS_SUCCESS,
                "message": "No matching results found for your query.",
                "data": [],
                "total_results": 0,
                "query": query
            }
            return JSONResponse(status_code=status.HTTP_200_OK, content=response)
        
        # Format results with relevance classification
        formatted_results = []
        for result in search_results:
            # Classify relevance based on distance score
            # Lower distance = higher relevance (L2 distance)
            distance = result["score"]
            if distance < 0.5:
                relevance = "high"
            elif distance < 1.0:
                relevance = "medium"
            else:
                relevance = "low"
            
            # Parse the document content (it's stored as JSON string)
            try:
                content = json.loads(result["document"]) if isinstance(result["document"], str) else result["document"]
            except json.JSONDecodeError:
                content = {"raw_content": result["document"]}
            
            formatted_results.append({
                "chunk_id": result["id"],
                "score": round(distance, 4),
                "content": content,
                "relevance": relevance
            })
        
        app_logger.info(f"Search completed - Found {len(formatted_results)} results")
        
        response = {
            "status": STATUS_SUCCESS,
            "message": f"Found {len(formatted_results)} matching results.",
            "data": formatted_results,
            "total_results": len(formatted_results),
            "query": query
        }
        
        return JSONResponse(status_code=status.HTTP_200_OK, content=response)
    
    except ValueError as e:
        # Handle validation errors (empty query, invalid parameters)
        app_logger.warning(f"Validation error during search: {e}")
        response = {
            "status": STATUS_FAILURE,
            "message": f"Invalid search request: {str(e)}",
            "data": [],
            "total_results": 0,
            "query": request_data.query
        }
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=response)
    
    except Exception as e:
        app_logger.exception("Error during search: %s", e)
        response = {
            "status": STATUS_FAILURE,
            "message": "Search failed. Please try again later.",
            "data": [],
            "total_results": 0,
            "query": request_data.query if request_data else ""
        }
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response)
