from typing import Any, Callable, Dict, List
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import Agent

from app.utils.logget_setup import ai_logger


class ToolRegistry:
    """Registry for managing tools available to agents."""
    
    def __init__(self):
        self._registry: Dict[str, Any] = {}
        ai_logger.debug("ToolRegistry initialized")

    def register_builtin(self, name: str, tool: BaseTool):
        """Register an ADK built-in tool (inheriting BaseTool)."""
        ai_logger.debug(f"Registering built-in tool '{name}' (type={type(tool).__name__})")
        self._registry[name] = tool

    def register_function(
        self,
        name: str,
        func: Callable,
        requires_confirmation: bool = False
    ):
        """
        Register a Python function as a tool.
        ADK wraps this automatically into a FunctionTool.
        """
        ai_logger.debug(f"Registering function tool '{name}' (func={func.__name__}, requires_confirmation={requires_confirmation})")
        try:
            tool = FunctionTool(func=func, require_confirmation=requires_confirmation)
            self._registry[name] = tool
            ai_logger.debug(f"Function tool '{name}' registered successfully")
        except Exception as e:
            ai_logger.error(f"Failed to register function tool '{name}': {str(e)}", exc_info=True)
            raise
        return self

    def register_agent_as_tool(self, name: str, agent: Agent):
        """
        Register another agent as a tool.
        That agent can be invoked like a tool by your main agent.
        """
        ai_logger.debug(f"Registering agent '{name}' as tool (agent_name={agent.name if hasattr(agent, 'name') else 'unknown'})")
        try:
            self._registry[name] = AgentTool(agent=agent)
            ai_logger.debug(f"Agent tool '{name}' registered successfully")
        except Exception as e:
            ai_logger.error(f"Failed to register agent as tool '{name}': {str(e)}", exc_info=True)
            raise
        return self

    def unregister(self, name: str):
        """Remove a tool from the registry."""
        if name in self._registry:
            self._registry.pop(name, None)
            ai_logger.debug(f"Tool '{name}' unregistered from registry")
        else:
            ai_logger.warning(f"Cannot unregister tool '{name}': tool not found in registry")
        return self

    def get_all(self) -> List[Any]:
        """Return all registered tools."""
        tools = list(self._registry.values())
        ai_logger.debug(f"Returning {len(tools)} registered tools")
        return tools

    def list_names(self) -> List[str]:
        """List names of registered tools."""
        names = list(self._registry.keys())
        ai_logger.debug(f"Tool registry contains: {names}")
        return names
