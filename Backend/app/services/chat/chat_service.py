"""
Chat Service using Multi-Agent System with Full Event Capture

This service handles user queries by routing them through
the multi-agent system and captures all reasoning/execution events.
"""

from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
from datetime import datetime
from google.adk.runners import Runner
from google.genai import types

from app.utils.logget_setup import app_logger
from app.core.configs.app_config import settings
from app.services.agents.agent_config import session_manager
from app.services.agents.multi_agent_system import MultiAgentSystem
from app.services.agents.agent_tools import search_index, retrieve_code_file, get_indexed_files, propose_code_change, load_index_for_folder
from app.services.agents.event_capture import ExecutionTrace, EventCapture, EventType


class ChatService:
    """
    Service responsible for processing user queries through the multi-agent system.
    
    Features:
    1. Multi-agent orchestration (Orchestrator + sub-agents)
    2. Full event capture for reasoning visibility
    3. Session management for conversation continuity
    """
    
    def __init__(self):
        self._multi_agent_system: Optional[MultiAgentSystem] = None
        self._runner: Optional[Runner] = None
        self._setup_agents()
    
    def _setup_agents(self):
        """Initialize the multi-agent system with tools."""
        try:
            # Create multi-agent system with all tools
            self._multi_agent_system = MultiAgentSystem(
                search_tool_func=search_index,
                retrieve_file_func=retrieve_code_file,
                list_files_func=get_indexed_files,
                propose_code_change_func=propose_code_change,
                compaction_interval=5,  # Compact every 5 invocations
                overlap_size=2          # Keep 2 invocations for context overlap
            )
            
            # Initialize and get the App (includes orchestrator + compaction config)
            app = self._multi_agent_system.initialize()
            
            # Initialize the runner with the App
            self._runner = Runner(
                app=app,
                session_service=session_manager.get_service()
            )
            
            app_logger.info("ChatService initialized with multi-agent system and context compaction")
            
        except Exception as e:
            app_logger.error(f"Failed to initialize ChatService: {str(e)}")
            raise
    
    async def process_query_stream(
        self,
        query: str,
        user_id: str,
        session_id: str,
        folder_id: Optional[str] = None,
        typing_delay: float = 0.02
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user query and stream events as they happen.
        
        Yields SSE events:
        - status: Current agent status/plan
        - thinking: Agent reasoning
        - tool_call: When a tool is invoked
        - tool_response: Tool results
        - token: Response text chunks (with typing delay)
        - complete: Final completion signal
        - error: Error information
        
        Args:
            query: The user's question or request
            user_id: User identifier
            session_id: Session identifier
            folder_id: Optional repository folder ID
            typing_delay: Delay between tokens for typing effect (seconds)
        """
        app_logger.info(f"Streaming query for user={user_id}, session={session_id}")
        
        # Load the appropriate FAISS index for this folder
        if folder_id:
            load_index_for_folder(folder_id)
        
        # Ensure session exists (get existing or create new)
        # Using "ReqioIQ" to match the App name configured in MultiAgentSystem
        await session_manager.get_or_create(settings.APP_NAME, user_id, session_id)
        
        # Create trace and event capture for consistent event handling
        trace = ExecutionTrace(
            session_id=session_id,
            user_id=user_id,
            query=query,
            started_at=datetime.utcnow().isoformat()
        )
        event_capture = EventCapture(trace)
        
        # Yield initial status
        yield {
            "event": "status",
            "data": {
                "status": "Starting query processing",
                "phase": "initialization"
            }
        }
        
        # Create user message
        user_message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )
        
        try:
            yield {
                "event": "status",
                "data": {
                    "status": "Analyzing your request",
                    "phase": "orchestration"
                }
            }
            
            async for event in self._runner.run_async(  # type: ignore
                user_id=user_id,
                session_id=session_id,
                new_message=user_message
            ):
                # Get the agent name from the event (defaults to orchestrator if not available)
                current_agent = getattr(event, 'author', 'orchestrator') or 'orchestrator'
                
                # Use EventCapture for consistent event parsing
                sse_events = event_capture.process_event_for_sse(event, current_agent=current_agent)
                
                for sse_event in sse_events:
                    if sse_event["event"] == EventType.FINAL_RESPONSE.value:
                        # Stream response text with typing effect
                        text = sse_event["data"].get("text", "")
                        for char in text:
                            yield {
                                "event": "token",
                                "data": {"token": char}
                            }
                            await asyncio.sleep(typing_delay)
                    else:
                        # Other events pass through directly
                        yield sse_event
            
            # Completion
            yield {
                "event": "complete",
                "data": {
                    "session_id": session_id,
                    "total_length": len(event_capture.get_accumulated_response())
                }
            }
            
        except Exception as e:
            error_msg = str(e) if str(e) else "An unexpected error occurred during processing"
            app_logger.error(f"Streaming error: {error_msg}", exc_info=True)
            yield {
                "event": "error",
                "data": {
                    "message": error_msg,
                    "type": type(e).__name__
                }
            }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the configured agents."""
        return {
            "orchestrator": {
                "name": "orchestrator",
                "model": settings.ANALYSIS_MODEL,
                "tools": self._multi_agent_system._tool_registry.list_names()
            },
            "answering_agent": {
                "name": "answering_agent",
                "model": settings.ANALYSIS_MODEL,
                "description": "Explains code and answers questions about the codebase"
            },
            "feature_generation_agent": {
                "name": "feature_generation_agent", 
                "model": settings.ANALYSIS_MODEL,
                "description": "Generates new code and features"
            }
        }
