from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

from app.utils.logget_setup import app_logger
from app.core.configs.app_config import system_config, REPO_STORAGE, helper_config
from app.schemas.feature_api_schemas import FileNode, ExplorerRequest, ContentRequest
from app.core.rate_limiter import limiter, EXPLORER_LIMIT

STATUS_SUCCESS = system_config.get("STATUS_SUCCESS", "success")
STATUS_FAILURE = system_config.get("STATUS_FAILURE", "failure")
IGNORE_EXTS = helper_config.get("ignore_extensions")
IGNORE_DIRS = helper_config.get("default_ignore")

router = APIRouter()


def build_tree(directory: Path, base_path: Path) -> list[FileNode]:
    """
    Recursively build a file tree from a directory.
    """
    nodes = []
    try:
        for item in sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            relative_path = str(item.relative_to(base_path)).replace("\\", "/")
            
            # Skip hidden files/folders and common non-essential directories
            if item.name.startswith(".") or item.name in IGNORE_DIRS or item.name.endswith(tuple(IGNORE_EXTS)):
                continue
            
            if item.is_dir():
                children = build_tree(item, base_path)
                nodes.append(FileNode(
                    name=item.name,
                    path=relative_path,
                    type="directory",
                    children=children
                ))
            else:
                nodes.append(FileNode(
                    name=item.name,
                    path=relative_path,
                    type="file",
                    children=None
                ))
    except PermissionError:
        app_logger.warning(f"Permission denied accessing: {directory}")
    except Exception as e:
        app_logger.error(f"Error building tree for {directory}: {e}")
    
    return nodes


@router.post("/explorer/tree")
@limiter.limit(EXPLORER_LIMIT)
async def get_repo_tree(request: Request, request_data: ExplorerRequest):
    """
    Get the file tree structure for an analyzed repository.
    
    Args:
        request_data: ExplorerRequest containing folder_id
        
    Returns:
        JSON tree structure of the repository
    """
    try:
        user_id = "918262"  # Hardcoded for now, should come from auth
        folder_id = request_data.folder_id
        
        repo_path = REPO_STORAGE / user_id / folder_id
        
        if not repo_path.exists():
            app_logger.warning(f"Repository not found: {repo_path}")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": STATUS_FAILURE,
                    "message": "Repository not found. Please analyze the repository first.",
                    "data": []
                }
            )
        
        tree = build_tree(repo_path, repo_path)
        
        app_logger.info(f"File tree built for {folder_id} with {len(tree)} top-level items")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": STATUS_SUCCESS,
                "message": "File tree retrieved successfully.",
                "data": [node.model_dump() for node in tree]
            }
        )
    
    except Exception as e:
        app_logger.exception(f"Error getting repo tree: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": STATUS_FAILURE,
                "message": "Failed to retrieve file tree.",
                "data": []
            }
        )


@router.post("/explorer/content")
@limiter.limit(EXPLORER_LIMIT)
async def get_file_content(request: Request, request_data: ContentRequest):
    """
    Get the content of a specific file in the repository.
    """
    try:
        user_id = "918262"
        folder_id = request_data.folder_id
        file_path = request_data.file_path.lstrip("/") # Remove leading slash if present
        
        repo_root = REPO_STORAGE / user_id / folder_id
        target_file = repo_root / file_path
        
        # Security check: Ensure file is within repo root
        try:
            target_file = target_file.resolve()
            repo_root = repo_root.resolve()
            if not str(target_file).startswith(str(repo_root)):
                raise ValueError("Path traversal attempt")
        except Exception:
             return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "status": STATUS_FAILURE,
                    "message": "Invalid file path.",
                    "data": None
                }
            )

        if not target_file.exists() or not target_file.is_file():
             return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": STATUS_FAILURE,
                    "message": "File not found.",
                    "data": None
                }
            )
            
        # Read content
        try:
            content = target_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Fallback for non-utf8 files (basic binary handling or skip)
            content = "[Binary or non-UTF-8 content cannot be displayed]"
            
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": STATUS_SUCCESS,
                "message": "File content retrieved.",
                "data": content
            }
        )

    except Exception as e:
        app_logger.exception(f"Error reading file {request_data.file_path}: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": STATUS_FAILURE,
                "message": "Failed to read file.",
                "data": None
            }
        )
