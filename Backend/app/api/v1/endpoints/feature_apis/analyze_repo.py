from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from app.schemas.feature_api_schemas import AnalysisRequest
from app.utils.logget_setup import app_logger
from app.core.configs.app_config import system_config, REPO_STORAGE
from app.services.github.code_analyzer import build_file_index, chunk_files

STATUS_SUCCESS = system_config.get("STATUS_SUCCESS", "success")
STATUS_FAILURE = system_config.get("STATUS_FAILURE", "failure")

router = APIRouter()


@router.post("/analysis")
async def analyze_repo(request: Request, request_data: AnalysisRequest):
    try:
        user_id = "918262"
        folder_ids = request_data.folder_ids[0]
        file_path = str(REPO_STORAGE / f"{user_id}" / f"{folder_ids}")
        
        indexed_file = build_file_index(file_path)
        if len(indexed_file) == 0:
            response = {"status": STATUS_FAILURE, "message": "No files found for analysis.", "data": []}
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)
        
        chunked_files = chunk_files(file_path, indexed_file)
        
        indexed_files = [
            f.model_dump(
                exclude_none=True,        # drop None fields
                by_alias=True,            # use field aliases
            ) if hasattr(f, "model_dump") else f
            for f in indexed_file
        ]
        
        final_data= {
            "indexed_files": indexed_files,
            "chunked_files": chunked_files
        }
        response = {"status": STATUS_SUCCESS, "message": "Analysis Completed!", "data": [final_data]}
        return JSONResponse(status_code=status.HTTP_200_OK, content=response)
        
    except Exception as e:
        app_logger.exception("Error while analyzing repository: %s", e)
        response = {"status": STATUS_FAILURE, "message": "Analysis Failed!", "data": []}
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response)