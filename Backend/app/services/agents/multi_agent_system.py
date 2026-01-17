"""
Multi-Agent System Setup for KreeperAI

This module creates and configures the multi-agent hierarchy:
- Orchestrator Agent: Routes queries and coordinates sub-agents
- Answering Agent: Explains code and answers questions about the codebase
- Feature Generation Agent: Generates new code/features

The agents communicate via ADK's AgentTool mechanism, allowing the orchestrator
to invoke sub-agents as tools.
"""

from typing import Dict, Any, List, Optional, Callable
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.function_tool import FunctionTool

from app.utils.logget_setup import app_logger
from app.core.configs.app_config import settings, prompt_config
from app.services.agents.manager.agent_manager import AgentManager
from app.services.agents.manager.tool_manager import ToolRegistry


class MultiAgentSystem:
    """
    Manages the multi-agent system for KreeperAI.
    
    Architecture:
    - Orchestrator (root agent) receives all user queries
    - Orchestrator has access to:
        - search_index tool (semantic search)
        - retrieve_code_file tool (file retrieval)
        - get_indexed_files tool (list indexed files)
        - answering_agent (AgentTool) - for code explanation
        - feature_generation_agent (AgentTool) - for code generation
    """
    
    def __init__(
        self, 
        search_tool_func: Optional[Callable] = None,
        retrieve_file_func: Optional[Callable] = None,
        list_files_func: Optional[Callable] = None
    ):
        self._agent_manager = AgentManager()
        self._tool_registry = ToolRegistry()
        self._orchestrator: Optional[LlmAgent] = None
        self._answering_agent: Optional[LlmAgent] = None
        self._feature_agent: Optional[LlmAgent] = None
        
        # Store tool functions
        self._search_tool_func = search_tool_func
        self._retrieve_file_func = retrieve_file_func
        self._list_files_func = list_files_func
        
        self._initialized = False
    
    def initialize(self) -> LlmAgent:
        """
        Initialize all agents and return the orchestrator.
        
        Returns:
            The orchestrator agent (root of the multi-agent system)
        """
        if self._initialized:
            return self._orchestrator
            
        app_logger.info("Initializing multi-agent system...")
        
        # Step 1: Register all function tools FIRST
        self._register_function_tools()
        
        # Step 2: Create specialized sub-agents
        self._create_answering_agent()
        self._create_feature_agent()
        
        # Step 3: Register sub-agents as tools
        self._register_agent_tools()
        
        # Step 4: Create orchestrator with all registered tools
        self._create_orchestrator()
        
        self._initialized = True
        app_logger.info("Multi-agent system initialized successfully")
        
        return self._orchestrator
    
    def _register_function_tools(self):
        """Register all function-based tools."""
        
        # Register search_index tool
        if self._search_tool_func:
            self._tool_registry.register_function(
                name="search_index",
                func=self._search_tool_func,
                requires_confirmation=False
            )
            app_logger.info("Registered search_index tool")
        
        # Register retrieve_code_file tool
        if self._retrieve_file_func:
            self._tool_registry.register_function(
                name="retrieve_code_file",
                func=self._retrieve_file_func,
                requires_confirmation=False
            )
            app_logger.info("Registered retrieve_code_file tool")
        
        # Register get_indexed_files tool
        if self._list_files_func:
            self._tool_registry.register_function(
                name="get_indexed_files",
                func=self._list_files_func,
                requires_confirmation=False
            )
            app_logger.info("Registered get_indexed_files tool")
    
    def _create_answering_agent(self):
        """Create the Answering Agent for code explanation queries."""
        answering_prompt = prompt_config.get("QUERY_ANSWERING_PROMPT", "")
        
        self._answering_agent = self._agent_manager.create(
            name="answering_agent",
            model=settings.FLASH_MODEL,
            instruction=answering_prompt,
            description=(
                "Answers questions about the codebase. Use this agent when the user "
                "wants to understand how existing code works, what a module does, "
                "or needs explanation of architecture and design patterns. "
                "Pass the user's question along with relevant repository context."
            ),
            tools=[]  # Answering agent has no sub-tools
        )
        
        app_logger.info("Answering agent created")
    
    def _create_feature_agent(self):
        """Create the Feature Generation Agent for code generation."""
        feature_prompt = prompt_config.get("FEATURE_GENERATION_PROMPT", "")
        
        self._feature_agent = self._agent_manager.create(
            name="feature_generation_agent",
            model=settings.ANALYSIS_MODEL,
            instruction=feature_prompt,
            description=(
                "Generates new code and features. Use this agent when the user "
                "wants to add new functionality, modify existing code, or implement "
                "new features. Pass the feature request along with relevant codebase context."
            ),
            tools=[]  # Feature agent has no sub-tools for now
        )
        
        app_logger.info("Feature generation agent created")
    
    def _register_agent_tools(self):
        """Register sub-agents as AgentTools for the orchestrator."""
        
        # Register answering agent
        self._tool_registry.register_agent_as_tool(
            name="answering_agent",
            agent=self._answering_agent
        )
        app_logger.info("Registered answering_agent as tool")
        
        # Register feature generation agent
        self._tool_registry.register_agent_as_tool(
            name="feature_generation_agent",
            agent=self._feature_agent
        )
        app_logger.info("Registered feature_generation_agent as tool")
    
    def _create_orchestrator(self):
        """Create the Orchestrator agent with all registered tools."""
        orchestrator_prompt = prompt_config.get("ORCHESTRATOR_PROMPT", "")
        
        all_tools = self._tool_registry.get_all()
        tool_names = self._tool_registry.list_names()
        
        self._orchestrator = self._agent_manager.create(
            name="orchestrator",
            model=settings.ANALYSIS_MODEL,
            instruction=orchestrator_prompt,
            description="Main orchestrator that routes queries to specialized agents",
            tools=all_tools
        )
        
        app_logger.info(f"Orchestrator agent created with {len(all_tools)} tools: {tool_names}")
    
    def get_orchestrator(self) -> LlmAgent:
        """Get the orchestrator agent."""
        if not self._initialized:
            return self.initialize()
        return self._orchestrator
    
    def get_answering_agent(self) -> LlmAgent:
        """Get the answering agent directly (for testing)."""
        return self._answering_agent
    
    def get_feature_agent(self) -> LlmAgent:
        """Get the feature generation agent directly (for testing)."""
        return self._feature_agent
    
    def get_tool_registry(self) -> ToolRegistry:
        """Get the tool registry for inspection."""
        return self._tool_registry
