from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from app.schemas.feature_api_schemas import ParseGithubUrl
from app.utils.logget_setup import app_logger
from app.services.github.parser import extract_github_info
from app.services.github.clone import clone_and_store

router = APIRouter()


@router.post("/parse_github_url")
async def parse_github_url(request: Request, request_data: ParseGithubUrl):
    try:
        user_id = "918262"
        url = request_data.github_repo
        parsed = extract_github_info(url)
        if not parsed:
            response = {
                "status": "failure",
                "message": "Unable to parse provided GitHub URL",
                "data": [],
            }
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=response)

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
