from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
import uuid

from google.genai.errors import ServerError

from app.schemas.feature_api_schemas import ChatRequest, ChatResponse
from app.utils.logget_setup import app_logger
from app.core.configs.app_config import system_config, settings
from app.services.agents.agent_config import agent_manager, session_manager, APP_NAME
from app.services.chat.chat_service import ChatService

STATUS_SUCCESS = system_config.get("STATUS_SUCCESS", "success")
STATUS_FAILURE = system_config.get("STATUS_FAILURE", "failure")

router = APIRouter()
chat_service = ChatService()


@router.post("/chat", status_code=status.HTTP_200_OK)
async def chat_with_agent(request: Request, request_data: ChatRequest):
    """
    Chat endpoint for user-agent conversations.
    
    Accepts a user query and processes it through the agent system,
    returning the agent's response.
    """
    try:
        app_logger.info(f"Chat request received: user_id={request_data.user_id}, session_id={request_data.session_id}")
        
        # Generate session_id if not provided
        session_id = request_data.session_id or str(uuid.uuid4())
        user_id = request_data.user_id or ""
        
        # Process the query through the chat service
        response = await chat_service.process_query(
            query=request_data.query,
            user_id=user_id,
            session_id=session_id,
            folder_id=request_data.folder_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": STATUS_SUCCESS,
                "message": "Query processed successfully",
                "data": {
                    "response": response.get("response", ""),
                    "session_id": session_id,
                    "user_id": user_id,
                    "metadata": response.get("metadata", {})
                }
            }
        )
        
    except ServerError as e:
        app_logger.error(f"Server error during chat: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": STATUS_FAILURE,
                "message": "AI service temporarily unavailable. Please try again.",
                "data": None
            }
        )
    except Exception as e:
        app_logger.error(f"Error processing chat request: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": STATUS_FAILURE,
                "message": f"Failed to process query: {str(e)}",
                "data": None
            }
        )
