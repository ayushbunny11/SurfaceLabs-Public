"""
Chat Service using Multi-Agent System with Full Event Capture

This service handles user queries by routing them through
the multi-agent system and captures all reasoning/execution events.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from google.adk.runners import Runner
from google.genai import types

from app.utils.logget_setup import app_logger
from app.core.configs.app_config import settings
from app.services.agents.agent_config import session_manager, APP_NAME
from app.services.agents.multi_agent_system import MultiAgentSystem
from app.services.agents.agent_tools import search_index, retrieve_code_file, get_indexed_files
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
                list_files_func=get_indexed_files
            )
            
            # Initialize and get the orchestrator
            orchestrator = self._multi_agent_system.initialize()
            
            # Initialize the runner with the orchestrator
            self._runner = Runner(
                agent=orchestrator,
                app_name=APP_NAME,
                session_service=session_manager.get_service()
            )
            
            app_logger.info("ChatService initialized with multi-agent system")
            
        except Exception as e:
            app_logger.error(f"Failed to initialize ChatService: {str(e)}")
            raise
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        folder_id: Optional[str] = None,
        capture_events: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent system.
        
        The orchestrator will:
        1. Analyze the query type (understanding vs feature request)
        2. Search the indexed repository for context
        3. Delegate to the appropriate sub-agent
        4. Return the synthesized response with full execution trace
        
        Args:
            query: The user's question or request
            user_id: User identifier
            session_id: Session identifier for conversation continuity
            folder_id: Optional repository folder ID for context
            capture_events: Whether to capture all execution events
            
        Returns:
            Dict containing the agent response, metadata, and execution trace
        """
        app_logger.info(f"Processing query for user={user_id}, session={session_id}")
        
        # Ensure session exists
        session = await session_manager.create(APP_NAME, user_id, session_id)
        
        # Create execution trace for event capture
        trace = ExecutionTrace(
            session_id=session_id,
            user_id=user_id,
            query=query,
            started_at=datetime.utcnow().isoformat()
        )
        
        # Add initial event
        trace.add_event(
            EventType.QUERY_RECEIVED,
            "system",
            {"query": query, "folder_id": folder_id}
        )
        
        # Create event capture processor
        event_capture = EventCapture(trace)
        
        # Create user message
        user_message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=query)]
        )
        
        try:
            async for event in self._runner.run_async(  # type: ignore
                user_id=user_id,
                session_id=session_id,
                new_message=user_message
            ):
                # Process each event through the capture system
                if capture_events:
                    event_capture.process_event(event, current_agent="orchestrator")
                
                # Also log key events for debugging
                if hasattr(event, 'author'):
                    app_logger.debug(f"[EVENT] Author: {event.author}")
            
            response_text = event_capture.get_accumulated_response()
            
            app_logger.info(
                f"Query processed for session={session_id}. "
                f"Events captured: {len(trace.events)}"
            )
            
        except Exception as e:
            app_logger.error(f"Error running multi-agent system: {str(e)}")
            trace.add_event(
                EventType.ERROR,
                "system",
                {"error": str(e)}
            )
            trace.error = str(e)
            trace.completed_at = datetime.utcnow().isoformat()
            raise
        
        return {
            "response": response_text,
            "execution_trace": trace.to_dict() if capture_events else None,
            "metadata": {
                "session_id": session_id,
                "user_id": user_id,
                "folder_id": folder_id,
                "events_count": len(trace.events),
                "tools_used": trace.to_dict()["summary"]["tools_used"],
                "agents_invoked": trace.to_dict()["summary"]["sub_agents_invoked"]
            }
        }
    
    async def process_direct_answering(
        self,
        query: str,
        context: str,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process a query directly through the answering agent (bypassing orchestrator).
        
        Useful for testing or when you know the query type upfront.
        """
        trace = ExecutionTrace(
            session_id=session_id,
            user_id=user_id,
            query=query,
            started_at=datetime.utcnow().isoformat()
        )
        event_capture = EventCapture(trace)
        
        answering_agent = self._multi_agent_system.get_answering_agent()
        
        # Create a runner for the answering agent directly
        answering_runner = Runner(
            agent=answering_agent,
            app_name=APP_NAME,
            session_service=session_manager.get_service()
        )
        
        # Build the prompt with context
        full_prompt = f"""## Repository Context
{context}

## User Question
{query}"""
        
        user_message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=full_prompt)]
        )
        
        trace.add_event(
            EventType.QUERY_RECEIVED,
            "answering_agent",
            {"query": query, "context_length": len(context)}
        )
        
        # Ensure session
        await session_manager.create(APP_NAME, user_id, session_id)
        
        async for event in answering_runner.run_async(  # type: ignore
            user_id=user_id,
            session_id=session_id,
            new_message=user_message
        ):
            event_capture.process_event(event, current_agent="answering_agent")
        
        response_text = event_capture.get_accumulated_response()
        
        return {
            "response": response_text,
            "execution_trace": trace.to_dict(),
            "metadata": {
                "agent": "answering_agent",
                "direct": True,
                "events_count": len(trace.events)
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
