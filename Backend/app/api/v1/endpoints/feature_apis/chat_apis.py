from fastapi import APIRouter, status, Request
from fastapi.responses import StreamingResponse
import json
import time

from app.schemas.feature_api_schemas import ChatRequest
from app.utils.logget_setup import app_logger
from app.services.chat.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/chat/stream", status_code=status.HTTP_200_OK)
async def chat_with_agent_stream(request: Request, request_data: ChatRequest):
    """
    SSE streaming chat endpoint for real-time agent responses.
    
    Streams events as they happen:
    - status: Current agent status/phase
    - thinking: Agent reasoning process
    - tool_call: Tool being invoked
    - tool_response: Tool results
    - token: Response text (streamed character by character)
    - complete: Completion signal with session_id
    - error: Error information
    
    Session Management:
    - If session_id is empty/null, a new session is created using user_id + folder_id + timestamp
    - The session_id is returned in the 'complete' event for frontend to store and reuse
    - To start a new session, simply send an empty session_id
    """
    app_logger.info(f"Stream chat request: user_id={request_data.user_id}, session_id={request_data.session_id}")
    
    user_id = request_data.user_id or "anonymous"
    folder_id = request_data.folder_id or "default"
    
    # Generate session_id if not provided (new session)
    if request_data.session_id:
        session_id = request_data.session_id
    else:
        # Create deterministic session ID: user_folder_timestamp
        session_id = f"{user_id}_{folder_id}_{int(time.time())}"
        app_logger.info(f"Created new session: {session_id}")
    
    async def event_generator():
        """Generate SSE events from the chat service."""
        try:
            async for event in chat_service.process_query_stream(
                query=request_data.query,
                user_id=user_id,
                session_id=session_id,
                folder_id=request_data.folder_id
            ):
                # Format as SSE
                event_type = event.get("event", "message")
                data = event.get("data", {})
                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                
        except Exception as e:
            app_logger.error(f"Stream error: {str(e)}")
            error_data = {"message": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Chat-Session-Id": session_id
        }
    )

