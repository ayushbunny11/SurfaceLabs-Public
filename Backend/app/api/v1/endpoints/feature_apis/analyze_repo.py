from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import uuid
from app.schemas.feature_api_schemas import AnalysisRequest
from app.utils.logget_setup import app_logger
from app.core.configs.app_config import system_config, REPO_STORAGE, settings
from app.services.github.code_analyzer import build_file_index, chunk_files, read_chunk
from app.services.agents.agent_config import agent_manager, memory_store, tool_registry, session_manager
STATUS_SUCCESS = system_config.get("STATUS_SUCCESS", "success")
STATUS_FAILURE = system_config.get("STATUS_FAILURE", "failure")

router = APIRouter()


@router.post("/analysis")
async def analyze_repo(request: Request, request_data: AnalysisRequest):
    try:
        user_id = "918262"
        folder_ids = request_data.folder_ids[0]
        file_path = str(REPO_STORAGE / f"{user_id}" / f"{folder_ids}")
        
        session_id = folder_ids
        
        chunk_file_path = Path(REPO_STORAGE) / str(user_id) / "chunks" / f"chunk_{session_id}.json"
        chunk_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        indexed_file_path = Path(REPO_STORAGE) / str(user_id) / "indexed_file" / f"file_index_{session_id}.json"
        indexed_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        indexed_file = build_file_index(file_path)
        if len(indexed_file) == 0:
            response = {"status": STATUS_FAILURE, "message": "No files found for analysis.", "data": []}
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)
        
        chunked_data = chunk_files(file_path, indexed_file)
        
        indexed_files = [
            f.model_dump(
                exclude_none=True,        # drop None fields
                by_alias=True,            # use field aliases
            ) if hasattr(f, "model_dump") else f
            for f in indexed_file
        ]
        
        try:
            chunk_file_path.write_text(json.dumps(chunked_data, indent=2), encoding="utf-8")
            indexed_file_path.write_text(json.dumps(indexed_files, indent=2), encoding="utf-8")
        except Exception as e:
            app_logger.exception("Failed to write chunk or indexed file: %s", e)
        
        
        files = read_chunk("chunk-3360afa9", "eedc058d684647f9880ac39bb87cba12")
        final_data= {
            "indexed_files": indexed_files,
            "chunked_files": chunked_data,
            "final_data": files
        }
        response = {"status": STATUS_SUCCESS, "message": "Analysis Completed!", "data": [final_data]}
        return JSONResponse(status_code=status.HTTP_200_OK, content=response)
        
    except Exception as e:
        app_logger.exception("Error while analyzing repository: %s", e)
        response = {"status": STATUS_FAILURE, "message": "Analysis Failed!", "data": []}
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response)