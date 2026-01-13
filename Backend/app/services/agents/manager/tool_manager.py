from typing import Any, Callable, Dict, List
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import Agent

class ToolRegistry:
    def __init__(self):
        self._registry: Dict[str, Any] = {}

    def register_builtin(self, name: str, tool: BaseTool):
        """Register an ADK built-in tool (inheriting BaseTool)."""
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
        tool = FunctionTool(func=func, require_confirmation=requires_confirmation)
        self._registry[name] = tool
        return self

    def register_agent_as_tool(self, name: str, agent: Agent):
        """
        Register another agent as a tool.
        That agent can be invoked like a tool by your main agent.
        """
        self._registry[name] = AgentTool(agent=agent)
        return self

    def unregister(self, name: str):
        """Remove a tool from the registry."""
        self._registry.pop(name, None)
        return self

    def get_all(self) -> List[Any]:
        """Return all registered tools."""
        return list(self._registry.values())

    def list_names(self) -> List[str]:
        """List names of registered tools."""
        return list(self._registry.keys())
