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

from app.utils.logget_setup import ai_logger
from app.core.configs.app_config import system_config


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
    TOKEN_USAGE = "token_usage"
    CODE_PROPOSAL = "code_proposal"  # For Diff Viewer integration


# User-friendly aliases for tools and agents
TOOL_ALIASES = {
    "get_indexed_files": "Checking repository structure",
    "search_index": "Searching codebase",
    "retrieve_code_file": "Reading file contents",
    "list_directory": "Browsing directory",
    "get_file_content": "Loading file",
    "propose_code_change": "Proposing code changes",
}

AGENT_ALIASES = {
    "orchestrator": "Task Manager",
    "answering_agent": "Response Assistant",
    "feature_generation_agent": "Feature Designer",
    "coding_agent": "Developer Assistant",
    "research_agent": "Research Analyst",
    "web_search_agent": "Google Assistant"
}

ERROR_MESSAGE = system_config.get("ERROR_MESSAGE", "An error occured!")

def get_tool_alias(tool_name: str) -> str:
    """Get user-friendly alias for a tool name."""
    alias = TOOL_ALIASES.get(tool_name, tool_name.replace("_", " ").title())
    ai_logger.debug(f"[ALIAS] Tool '{tool_name}' -> '{alias}'")
    return alias


def get_agent_alias(agent_name: str) -> str:
    """Get user-friendly alias for an agent name."""
    alias = AGENT_ALIASES.get(agent_name, agent_name.replace("_", " ").title())
    ai_logger.debug(f"[ALIAS] Agent '{agent_name}' -> '{alias}'")
    return alias


def summarize_tool_response(tool_name: str, response_str: str) -> str:
    """Generate a user-friendly summary of a tool response."""
    ai_logger.debug(f"[SUMMARIZE] Summarizing response for tool '{tool_name}' (response_length={len(response_str)})")
    
    try:
        # User-friendly aliases for agents if it's an agent calling an agent
        is_agent = 'agent' in tool_name.lower()
        
        # Parse common patterns from responses
        if "get_indexed_files" in tool_name:
            if "Total indexed documents:" in response_str:
                import re
                match = re.search(r'Total indexed documents:\s*(\d+)', response_str)
                if match:
                    summary = f"Found {match.group(1)} indexed files"
                    ai_logger.debug(f"[SUMMARIZE] Generated summary: '{summary}'")
                    return summary
            return "Checked index"
        
        elif "search_index" in tool_name:
            if "Found" in response_str and "relevant" in response_str:
                import re
                match = re.search(r'Found\s+(\d+)\s+relevant', response_str)
                if match:
                    summary = f"Found {match.group(1)} relevant results"
                    ai_logger.debug(f"[SUMMARIZE] Generated summary: '{summary}'")
                    return summary
            return "Search complete"
        
        elif "retrieve_code_file" in tool_name or "get_file_content" in tool_name:
            import re
            match = re.search(r'━+\s*([^\s━]+)\s*━+', response_str)
            if match:
                summary = f"Loaded {match.group(1)}"
                ai_logger.debug(f"[SUMMARIZE] Generated summary: '{summary}'")
                return summary
            return "File loaded"
        
        elif is_agent:
            # If it's an agent, try to see if it's actually "complete" or just "ready"
            if len(response_str) > 10:
                return "Provided findings"
            return "Analysis complete"
        
        else:
            return "Analyzing final response..."
            
    except Exception as e:
        ai_logger.warning(f"[SUMMARIZE] Failed to summarize tool response: {str(e)}")
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
        ai_logger.debug(f"[TRACE] {event_type.value}: {agent_name} - {str(content)[:200]}")
    
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
        ai_logger.debug(f"[EventCapture] Initialized for session={trace.session_id}, user={trace.user_id}")
    
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
        ai_logger.debug(f"[EventCapture] Processing event from agent='{current_agent}'")
        
        try:
            # Check for function calls (tool invocations)
            function_calls = event.get_function_calls() if hasattr(event, 'get_function_calls') else None
            if function_calls:
                ai_logger.debug(f"[EventCapture] Found {len(function_calls)} function call(s)")
                for call in function_calls:
                    tool_name = call.name if hasattr(call, 'name') else str(call)
                    is_agent = 'agent' in tool_name.lower() or any(a in tool_name.lower() for a in ["orchestrator", "assistant", "system", "manager"])
                    
                    ai_logger.debug(f"[EventCapture] Function call: tool='{tool_name}', is_agent={is_agent}")
                    
                    # Get user-friendly aliases
                    tool_alias = get_agent_alias(tool_name) if is_agent else get_tool_alias(tool_name)
                    agent_alias = get_agent_alias(current_agent)
                    
                    # Extract arguments for more descriptive status messages
                    tool_args = {}
                    if hasattr(call, 'args') and call.args:
                        try:
                            tool_args = call.args if isinstance(call.args, dict) else {}
                            ai_logger.debug(f"[EventCapture] tool_args: {tool_args}")
                        except:
                            pass
                    
                    if is_agent:
                        status_msg = f"{agent_alias} is consulting {tool_alias}..."
                    
                    elif "microsoft" in tool_name.lower() or "learn" in tool_name.lower():
                        ai_logger.debug(f"[EventCapture] Function call: tool='{tool_name}', is_agent={is_agent}")
                        status_msg = f"Fetching data from {tool_alias} MCP server..."
                    
                    elif "google_search" in tool_name.lower():
                        ai_logger.debug(f"[EventCapture] Function call: tool='{tool_name}', is_agent={is_agent}")
                        search_query = tool_args.get('query', '') or tool_args.get('q', '')
                        ai_logger.debug(f"[EventCapture] search_query: {search_query}")
                        if search_query:
                            
                            query_preview = search_query[:60] + "..." if len(search_query) > 60 else search_query
                            status_msg = f"Searching Web for {query_preview}"
                        else:
                            status_msg = "Searching Web"
                    else:
                        status_msg = f"{tool_alias} to help process request"
                    
                    # Only send status if it's meaningful and different
                    if status_msg != self._last_status:
                        ai_logger.debug(f"[EventCapture] Emitting status: '{status_msg}'")
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
                    ai_logger.debug(f"[EventCapture] Emitting {event_type.value} event for '{tool_alias}'")
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
                ai_logger.debug(f"[EventCapture] Found {len(function_responses)} function response(s)")
                for response in function_responses:
                    tool_name = response.name if hasattr(response, 'name') else "unknown"
                    # Keep full response for propose_code_change, truncate for others
                    full_response = response.response if hasattr(response, 'response') else None
                    result = str(full_response)[:1000] if full_response else ""
                    is_agent = 'agent' in tool_name.lower() or any(a in tool_name.lower() for a in ["orchestrator", "assistant", "system", "manager"])
                    
                    ai_logger.debug(f"[EventCapture] Function response: tool='{tool_name}', response_length={len(result)}")
                    
                    # Get aliases and summarize response
                    tool_alias = get_agent_alias(tool_name) if is_agent else get_tool_alias(tool_name)
                    response_summary = summarize_tool_response(tool_name, result)
                    
                    event_type = EventType.SUB_AGENT_RESPONSE if is_agent else EventType.TOOL_RESPONSE
                    ai_logger.debug(f"[EventCapture] Emitting {event_type.value} event: summary='{response_summary}'")
                    sse_events.append({
                        "event": event_type.value,
                        "data": {
                            "tool_name": tool_alias,
                            "response_summary": response_summary
                        }
                    })
                    
                    # Special handling for propose_code_change - emit code_proposal event
                    if tool_name == "propose_code_change" and full_response:
                        try:
                            # Use the full response object directly (it's a dict)
                            response_data = full_response if isinstance(full_response, dict) else None
                            if response_data and response_data.get("success"):
                                ai_logger.info(f"[EventCapture] Emitting CODE_PROPOSAL for {response_data.get('file_path')}")
                                sse_events.append({
                                    "event": EventType.CODE_PROPOSAL.value,
                                    "data": {
                                        "file_path": response_data.get("file_path"),
                                        "original_content": response_data.get("original_content"),
                                        "proposed_content": response_data.get("proposed_content"),
                                        "proposal_id": response_data.get("proposal_id")
                                    }
                                })
                            elif response_data and not response_data.get("success"):
                                ai_logger.warning(f"[EventCapture] propose_code_change failed: {response_data.get('error')}")
                        except Exception as parse_err:
                            ai_logger.warning(f"[EventCapture] Failed to process propose_code_change response: {parse_err}")
            
            # Check for usage metadata (token counts)
            if hasattr(event, 'usage_metadata') and event.usage_metadata:
                usage = event.usage_metadata
                # ai_logger.debug(f"[TOKEN_USAGE] {usage}")
                prompt_tokens = getattr(usage, 'prompt_token_count', 0) or 0
                candidates_tokens = getattr(usage, 'candidates_token_count', 0) or 0
                total_tokens = getattr(usage, 'total_token_count', 0) or 0
                thoughts_tokens = getattr(usage, 'thoughts_token_count', 0) or 0
                cached_tokens = getattr(usage, 'cached_content_token_count', 0) or 0
                
                ai_logger.info(
                    f"[TOKEN_USAGE] Prompt: {prompt_tokens}, "
                    f"Candidates: {candidates_tokens}, "
                    f"Thoughts: {thoughts_tokens}, "
                    f"Cached: {cached_tokens}, "
                    f"Total: {total_tokens}"
                )
                
                sse_events.append({
                    "event": EventType.TOKEN_USAGE.value,
                    "data": {
                        "prompt_tokens": prompt_tokens,
                        "candidates_tokens": candidates_tokens,
                        "thoughts_tokens": thoughts_tokens,
                        "cached_tokens": cached_tokens,
                        "total_tokens": total_tokens
                    }
                })
            
            # Check for text content (agent thinking/responses)
            if event.content and event.content.parts:
                ai_logger.debug(f"[EventCapture] Processing {len(event.content.parts)} content part(s)")
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_length = len(part.text)
                        is_final = event.is_final_response()
                        ai_logger.debug(f"[EventCapture] Text content: length={text_length}, is_final={is_final}")
                        
                        if is_final:
                            self._accumulated_text += part.text
                            ai_logger.debug(f"[EventCapture] Emitting FINAL_RESPONSE (accumulated_length={len(self._accumulated_text)})")
                            sse_events.append({
                                "event": EventType.FINAL_RESPONSE.value,
                                "data": {
                                    "text": part.text,
                                    "is_final": True
                                }
                            })
                        else:
                            if not function_calls and not function_responses:
                                agent_alias = get_agent_alias(current_agent)
                                thought_preview = part.text.strip()
                                if thought_preview and len(thought_preview) > 10:
                                    status_preview = thought_preview[:60].replace("\n", " ") + "..."
                                    ai_logger.debug(f"[EventCapture] Agent thinking: '{status_preview}'")
                                    sse_events.append({
                                        "event": "status",
                                        "data": {
                                            "status": f"Analyzing: {status_preview}",
                                            "phase": "thinking",
                                            "agent": agent_alias
                                        }
                                    })
                                
                                ai_logger.debug(f"[EventCapture] Emitting AGENT_THINKING event")
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
                ai_logger.error(f"Agent error detected: {event.error_code} - {error_msg}")
                sse_events.append({
                    "event": EventType.ERROR.value,
                    "data": {
                        "error_code": event.error_code,
                        "message": ERROR_MESSAGE
                    }
                })
            
            # Check for state changes
            if hasattr(event, 'actions') and event.actions:
                if event.actions.state_delta:
                    ai_logger.debug(f"[EventCapture] State change detected: {str(event.actions.state_delta)[:100]}")
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
                    ai_logger.debug(f"[EventCapture] Found {len(metadata.grounding_chunks)} grounding chunk(s)")
                    for chunk in metadata.grounding_chunks:
                        citation_data = {}
                        if hasattr(chunk, 'web') and chunk.web:
                            citation_data = {
                                "title": chunk.web.title,
                                "uri": chunk.web.uri,
                                "type": "web"
                            }
                            ai_logger.debug(f"[EventCapture] Web citation: {chunk.web.title}")
                        elif hasattr(chunk, 'retrieved_context') and chunk.retrieved_context:
                            citation_data = {
                                "title": chunk.retrieved_context.title,
                                "uri": chunk.retrieved_context.uri,
                                "type": "retrieval"
                            }
                            ai_logger.debug(f"[EventCapture] Retrieval citation: {chunk.retrieved_context.title}")
                        
                        if citation_data:
                            sse_events.append({
                                "event": EventType.CITATION.value,
                                "data": {
                                    "citation": citation_data,
                                    "agent": current_agent
                                }
                            })
                
        except Exception as e:
            ai_logger.error(f"[EventCapture] Error processing event for SSE: {str(e)}", exc_info=True)
            sse_events.append({
                "event": EventType.ERROR.value,
                "data": {"message": str(e)}
            })
        
        ai_logger.debug(f"[EventCapture] Returning {len(sse_events)} SSE event(s)")
        return sse_events
    
    def get_accumulated_response(self) -> str:
        """Get the accumulated response text."""
        ai_logger.debug(f"[EventCapture] Returning accumulated response (length={len(self._accumulated_text)})")
        return self._accumulated_text
