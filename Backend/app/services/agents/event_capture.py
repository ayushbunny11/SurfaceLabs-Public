"""
Agent Event Capture System

Captures and structures all events from the multi-agent system including:
- Agent reasoning/thinking
- Tool calls and responses
- Sub-agent invocations
- Final responses
- Errors

This provides full visibility into the agent's decision-making process.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.utils.logget_setup import app_logger


class EventType(str, Enum):
    """Types of events in the agent execution flow."""
    QUERY_RECEIVED = "query_received"
    AGENT_THINKING = "agent_thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    SUB_AGENT_CALL = "sub_agent_call"
    SUB_AGENT_RESPONSE = "sub_agent_response"
    FINAL_RESPONSE = "final_response"
    ERROR = "error"
    STATE_CHANGE = "state_change"
    CITATION = "citation"


# User-friendly aliases for tools and agents
TOOL_ALIASES = {
    "get_indexed_files": "Checking repository structure",
    "search_index": "Searching codebase",
    "retrieve_code_file": "Reading file contents",
    "list_directory": "Browsing directory",
    "get_file_content": "Loading file",
}

AGENT_ALIASES = {
    "orchestrator": "Task Manager",
    "answering_agent": "Response Assistant",
    "feature_generation_agent": "Feature Designer",
    "coding_agent": "Developer Assistant",
    "research_agent": "Research Analyst",
}


def get_tool_alias(tool_name: str) -> str:
    """Get user-friendly alias for a tool name."""
    return TOOL_ALIASES.get(tool_name, tool_name.replace("_", " ").title())


def get_agent_alias(agent_name: str) -> str:
    """Get user-friendly alias for an agent name."""
    return AGENT_ALIASES.get(agent_name, agent_name.replace("_", " ").title())


def summarize_tool_response(tool_name: str, response_str: str) -> str:
    """Generate a user-friendly summary of a tool response."""
    try:
        # User-friendly aliases for agents if it's an agent calling an agent
        is_agent = 'agent' in tool_name.lower()
        
        # Parse common patterns from responses
        if "get_indexed_files" in tool_name:
            if "Total indexed documents:" in response_str:
                import re
                match = re.search(r'Total indexed documents:\s*(\d+)', response_str)
                if match:
                    return f"Found {match.group(1)} indexed files"
            return "Checked index"
        
        elif "search_index" in tool_name:
            if "Found" in response_str and "relevant" in response_str:
                import re
                match = re.search(r'Found\s+(\d+)\s+relevant', response_str)
                if match:
                    return f"Found {match.group(1)} relevant results"
            return "Search complete"
        
        elif "retrieve_code_file" in tool_name or "get_file_content" in tool_name:
            import re
            match = re.search(r'━+\s*([^\s━]+)\s*━+', response_str)
            if match:
                return f"Loaded {match.group(1)}"
            return "File loaded"
        
        elif is_agent:
            # If it's an agent, try to see if it's actually "complete" or just "ready"
            if len(response_str) > 10:
                return "Provided findings"
            return "Analysis complete"
        
        else:
            return "Task finished"
            
    except Exception:
        return "Complete"


@dataclass
class AgentEvent:
    """Represents a single event in the agent execution flow."""
    event_type: EventType
    timestamp: str
    agent_name: str
    content: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "timestamp": self.timestamp,
            "agent": self.agent_name,
            "content": self.content
        }


@dataclass 
class ExecutionTrace:
    """
    Complete trace of an agent execution session.
    Captures all events in order for debugging and visualization.
    """
    session_id: str
    user_id: str
    query: str
    started_at: str
    events: List[AgentEvent] = field(default_factory=list)
    final_response: str = ""
    completed_at: Optional[str] = None
    error: Optional[str] = None
    
    def add_event(
        self,
        event_type: EventType,
        agent_name: str,
        content: Dict[str, Any]
    ):
        """Add a new event to the trace."""
        event = AgentEvent(
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            agent_name=agent_name,
            content=content
        )
        self.events.append(event)
        app_logger.debug(f"[TRACE] {event_type.value}: {agent_name} - {str(content)[:200]}")
    
class EventCapture:
    """
    Processes ADK events and populates an ExecutionTrace.
    """
    
    def __init__(self, trace: ExecutionTrace):
        self.trace = trace
        self._accumulated_text = ""
        # State tracking for deduplication
        self._last_status = ""
        self._last_tool_action = ""  # tool_name + type
    
    def process_event_for_sse(self, event, current_agent: str = "orchestrator") -> List[Dict[str, Any]]:
        """
        Process an ADK event and return SSE-formatted events.
        
        Returns a list of SSE events (may be multiple per ADK event).
        Each event has: {"event": str, "data": dict}
        
        Args:
            event: ADK Event object
            current_agent: Name of the current agent processing
            
        Returns:
            List of SSE event dictionaries
        """
        sse_events = []
        
        try:
            # Check for function calls (tool invocations)
            function_calls = event.get_function_calls() if hasattr(event, 'get_function_calls') else None
            if function_calls:
                for call in function_calls:
                    tool_name = call.name if hasattr(call, 'name') else str(call)
                    is_agent = 'agent' in tool_name.lower() or any(a in tool_name.lower() for a in ["orchestrator", "assistant", "system", "manager"])
                    
                    # Get user-friendly aliases
                    tool_alias = get_agent_alias(tool_name) if is_agent else get_tool_alias(tool_name)
                    agent_alias = get_agent_alias(current_agent)
                    
                    # Status update - provide context rather than just mirroring the call
                    if is_agent:
                        status_msg = f"{agent_alias} is consulting {tool_alias}..."
                    else:
                        status_msg = f"Using {tool_alias} to help process request"
                    
                    # Only send status if it's meaningful and different
                    if status_msg != self._last_status:
                        sse_events.append({
                            "event": "status",
                            "data": {
                                "status": status_msg,
                                "phase": "execution",
                                "agent": agent_alias
                            }
                        })
                        self._last_status = status_msg
                    
                    # Tool/Sub-agent call event
                    event_type = EventType.SUB_AGENT_CALL if is_agent else EventType.TOOL_CALL
                    sse_events.append({
                        "event": event_type.value,
                        "data": {
                            "tool_name": tool_alias,
                            "is_agent": is_agent
                        }
                    })
            
            # Check for function responses
            function_responses = event.get_function_responses() if hasattr(event, 'get_function_responses') else None
            if function_responses:
                for response in function_responses:
                    tool_name = response.name if hasattr(response, 'name') else "unknown"
                    result = str(response.response)[:1000] if hasattr(response, 'response') else ""
                    is_agent = 'agent' in tool_name.lower() or any(a in tool_name.lower() for a in ["orchestrator", "assistant", "system", "manager"])
                    
                    # Get aliases and summarize response
                    tool_alias = get_agent_alias(tool_name) if is_agent else get_tool_alias(tool_name)
                    response_summary = summarize_tool_response(tool_name, result)
                    
                    event_type = EventType.SUB_AGENT_RESPONSE if is_agent else EventType.TOOL_RESPONSE
                    sse_events.append({
                        "event": event_type.value,
                        "data": {
                            "tool_name": tool_alias,
                            "response_summary": response_summary
                        }
                    })
            
            # Check for text content (agent thinking/responses)
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        if event.is_final_response():
                            # For final response, return the text chunk for streaming
                            self._accumulated_text += part.text
                            sse_events.append({
                                "event": EventType.FINAL_RESPONSE.value,
                                "data": {
                                    "text": part.text,
                                    "is_final": True
                                }
                            })
                        else:
                            # Intermediate reasoning (less strict detection)
                            # Only treat as thought if it's not part of a tool call/response event
                            # that we already handled
                            if not function_calls and not function_responses:
                                agent_alias = get_agent_alias(current_agent)
                                
                                # Show a snippet in status if it looks like reasoning
                                thought_preview = part.text.strip()
                                if thought_preview and len(thought_preview) > 10:
                                    status_preview = thought_preview[:60].replace("\n", " ") + "..."
                                    sse_events.append({
                                        "event": "status",
                                        "data": {
                                            "status": f"Analyzing: {status_preview}",
                                            "phase": "thinking",
                                            "agent": agent_alias
                                        }
                                    })
                                
                                sse_events.append({
                                    "event": EventType.AGENT_THINKING.value,
                                    "data": {
                                        "thought": part.text[:1000] + ("..." if len(part.text) > 1000 else ""),
                                        "agent": current_agent
                                    }
                                })
            
            # Handle errors
            if hasattr(event, 'error_code') and event.error_code:
                error_msg = event.error_message or f"Agent encountered an error ({event.error_code})"
                app_logger.error(f"Agent error detected: {event.error_code} - {error_msg}")
                sse_events.append({
                    "event": EventType.ERROR.value,
                    "data": {
                        "error_code": event.error_code,
                        "message": error_msg
                    }
                })
            
            # Check for state changes
            if hasattr(event, 'actions') and event.actions:
                if event.actions.state_delta:
                    sse_events.append({
                        "event": EventType.STATE_CHANGE.value,
                        "data": {
                            "state_delta": str(event.actions.state_delta),
                            "agent": current_agent
                        }
                    })
                
            # Check for grounding metadata (citations)
            if hasattr(event, 'grounding_metadata') and event.grounding_metadata:
                metadata = event.grounding_metadata
                if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                    for chunk in metadata.grounding_chunks:
                        citation_data = {}
                        if hasattr(chunk, 'web') and chunk.web:
                            citation_data = {
                                "title": chunk.web.title,
                                "uri": chunk.web.uri,
                                "type": "web"
                            }
                        elif hasattr(chunk, 'retrieved_context') and chunk.retrieved_context:
                            citation_data = {
                                "title": chunk.retrieved_context.title,
                                "uri": chunk.retrieved_context.uri,
                                "type": "retrieval"
                            }
                        
                        if citation_data:
                            sse_events.append({
                                "event": EventType.CITATION.value,
                                "data": {
                                    "citation": citation_data,
                                    "agent": current_agent
                                }
                            })
                
        except Exception as e:
            app_logger.error(f"Error processing event for SSE: {str(e)}")
            sse_events.append({
                "event": EventType.ERROR.value,
                "data": {"message": str(e)}
            })
        
        return sse_events
    
    def get_accumulated_response(self) -> str:
        """Get the accumulated response text."""
        return self._accumulated_text
