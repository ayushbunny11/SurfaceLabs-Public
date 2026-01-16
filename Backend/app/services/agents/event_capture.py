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
    PARTIAL_RESPONSE = "partial_response"
    FINAL_RESPONSE = "final_response"
    ERROR = "error"
    STATE_CHANGE = "state_change"


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "query": self.query,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "events": [e.to_dict() for e in self.events],
            "final_response": self.final_response,
            "error": self.error,
            "summary": self._generate_summary()
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of the execution."""
        tool_calls = [e for e in self.events if e.event_type == EventType.TOOL_CALL]
        sub_agent_calls = [e for e in self.events if e.event_type == EventType.SUB_AGENT_CALL]
        
        return {
            "total_events": len(self.events),
            "tools_used": list(set(e.content.get("tool_name", "") for e in tool_calls)),
            "sub_agents_invoked": list(set(e.content.get("agent_name", "") for e in sub_agent_calls)),
            "had_error": self.error is not None
        }


class EventCapture:
    """
    Processes ADK events and populates an ExecutionTrace.
    """
    
    def __init__(self, trace: ExecutionTrace):
        self.trace = trace
        self._accumulated_text = ""
    
    def process_event(self, event, current_agent: str = "orchestrator"):
        """
        Process an ADK event and add it to the trace.
        
        Args:
            event: ADK Event object
            current_agent: Name of the current agent processing
        """
        try:
            # Check for function calls (tool invocations)
            function_calls = event.get_function_calls() if hasattr(event, 'get_function_calls') else None
            if function_calls:
                for call in function_calls:
                    tool_name = call.name if hasattr(call, 'name') else str(call)
                    args = call.args if hasattr(call, 'args') else {}
                    
                    # Determine if this is a sub-agent call or regular tool
                    if 'agent' in tool_name.lower():
                        self.trace.add_event(
                            EventType.SUB_AGENT_CALL,
                            current_agent,
                            {
                                "agent_name": tool_name,
                                "input": args
                            }
                        )
                    else:
                        self.trace.add_event(
                            EventType.TOOL_CALL,
                            current_agent,
                            {
                                "tool_name": tool_name,
                                "arguments": args
                            }
                        )
            
            # Check for function responses
            function_responses = event.get_function_responses() if hasattr(event, 'get_function_responses') else None
            if function_responses:
                for response in function_responses:
                    tool_name = response.name if hasattr(response, 'name') else "unknown"
                    result = str(response.response)[:500] if hasattr(response, 'response') else ""
                    
                    if 'agent' in tool_name.lower():
                        self.trace.add_event(
                            EventType.SUB_AGENT_RESPONSE,
                            current_agent,
                            {
                                "agent_name": tool_name,
                                "response_preview": result
                            }
                        )
                    else:
                        self.trace.add_event(
                            EventType.TOOL_RESPONSE,
                            current_agent,
                            {
                                "tool_name": tool_name,
                                "response_preview": result
                            }
                        )
            
            # Check for text content (agent thinking/responses)
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        if event.is_final_response():
                            self._accumulated_text += part.text
                        elif not function_calls and not function_responses:
                            # This is intermediate agent reasoning
                            self.trace.add_event(
                                EventType.AGENT_THINKING,
                                current_agent,
                                {
                                    "thought": part.text[:500] + ("..." if len(part.text) > 500 else "")
                                }
                            )
            
            # Check for state changes
            if hasattr(event, 'actions') and event.actions:
                if event.actions.state_delta:
                    self.trace.add_event(
                        EventType.STATE_CHANGE,
                        current_agent,
                        {"state_delta": str(event.actions.state_delta)}
                    )
            
            # Handle final response
            if event.is_final_response():
                self.trace.add_event(
                    EventType.FINAL_RESPONSE,
                    current_agent,
                    {"response_length": len(self._accumulated_text)}
                )
                self.trace.final_response = self._accumulated_text
                self.trace.completed_at = datetime.utcnow().isoformat()
            
            # Handle errors
            if hasattr(event, 'error_code') and event.error_code:
                self.trace.add_event(
                    EventType.ERROR,
                    current_agent,
                    {
                        "error_code": event.error_code,
                        "error_message": event.error_message or ""
                    }
                )
                self.trace.error = event.error_message
                
        except Exception as e:
            app_logger.error(f"Error processing event: {str(e)}")
    
    def get_accumulated_response(self) -> str:
        """Get the accumulated response text."""
        return self._accumulated_text
