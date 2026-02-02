"""
API endpoint for downloading a repository as a ZIP file.
"""
import io
import zipfile
from pathlib import Path

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse, StreamingResponse

from app.utils.logget_setup import app_logger
from app.core.configs.app_config import system_config, REPO_STORAGE, helper_config
from app.schemas.feature_api_schemas import ExplorerRequest

STATUS_SUCCESS = system_config.get("STATUS_SUCCESS", "success")
STATUS_FAILURE = system_config.get("STATUS_FAILURE", "failure")
IGNORE_DIRS = helper_config.get("default_ignore", [".git", "__pycache__", "node_modules"])

router = APIRouter()


def create_zip_from_directory(directory: Path) -> io.BytesIO:
    """
    Create an in-memory ZIP archive from a directory.
    
    Args:
        directory: Path to the directory to zip
        
    Returns:
        BytesIO object containing the ZIP file
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in directory.rglob("*"):
            # Skip ignored directories
            relative_path = file_path.relative_to(directory)
            parts = relative_path.parts
            
            # Check if any part of the path is in IGNORE_DIRS
            if any(part in IGNORE_DIRS or part.startswith(".") for part in parts):
                continue
            
            # Only add files (directories are created automatically)
            if file_path.is_file():
                arcname = str(relative_path)
                try:
                    zip_file.write(file_path, arcname)
                except Exception as e:
                    app_logger.warning(f"Could not add {file_path} to zip: {e}")
    
    zip_buffer.seek(0)
    return zip_buffer


@router.post("/download/repo")
async def download_repo(request_data: ExplorerRequest):
    """
    Download a repository as a ZIP file.
    
    Args:
        request_data: ExplorerRequest containing folder_id
        
    Returns:
        StreamingResponse with the ZIP file
    """
    try:
        user_id = "918262"  # Hardcoded for now, should come from auth
        folder_id = request_data.folder_id
        
        repo_path = REPO_STORAGE / user_id / folder_id
        
        if not repo_path.exists() or not repo_path.is_dir():
            app_logger.warning(f"Repository not found: {repo_path}")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": STATUS_FAILURE,
                    "message": "Repository not found. Please analyze the repository first.",
                    "data": None
                }
            )
        
        # Security check: Ensure path is within REPO_STORAGE
        try:
            resolved_path = repo_path.resolve()
            storage_resolved = REPO_STORAGE.resolve()
            if not str(resolved_path).startswith(str(storage_resolved)):
                raise ValueError("Path traversal attempt")
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "status": STATUS_FAILURE,
                    "message": "Invalid folder ID.",
                    "data": None
                }
            )
        
        # Create ZIP archive
        app_logger.info(f"Creating ZIP archive for {folder_id}")
        zip_buffer = create_zip_from_directory(repo_path)
        
        # Generate a meaningful filename
        zip_filename = f"repo_{folder_id}.zip"
        
        app_logger.info(f"Sending ZIP archive: {zip_filename}")
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_filename}"'
            }
        )
    
    except Exception as e:
        app_logger.exception(f"Error downloading repository: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": STATUS_FAILURE,
                "message": "Failed to create repository archive.",
                "data": None
            }
        )
