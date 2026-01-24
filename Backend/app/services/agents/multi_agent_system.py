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
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.tools import google_search

from app.utils.logget_setup import ai_logger
from app.core.configs.app_config import settings, prompt_config
from app.services.agents.manager.agent_manager import AgentManager
from app.services.agents.manager.tool_manager import ToolRegistry
from app.services.agents.mcp.prebuilt_mcps import _microsoft_learn_mcp_toolset


PROMPT_GUIDELINES = prompt_config.get("PROMPT_GUIDELINES", "")

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
        list_files_func: Optional[Callable] = None,
        propose_code_change_func: Optional[Callable] = None,
        compaction_interval: int = 5,
        overlap_size: int = 2
    ):
        ai_logger.debug("Initializing MultiAgentSystem...")
        ai_logger.debug(f"Compaction settings: interval={compaction_interval}, overlap={overlap_size}")
        
        self._agent_manager = AgentManager()
        self._tool_registry = ToolRegistry()
        self._orchestrator: Optional[LlmAgent] = None
        self._answering_agent: Optional[LlmAgent] = None
        self._feature_agent: Optional[LlmAgent] = None
        self._web_search_agent: Optional[LlmAgent] = None
        self._app: Optional[App] = None
        
        # Store tool functions
        self._search_tool_func = search_tool_func
        self._retrieve_file_func = retrieve_file_func
        self._list_files_func = list_files_func
        self._propose_code_change_func = propose_code_change_func
        
        # Log tool function availability
        ai_logger.debug(f"Tool functions provided: search={search_tool_func is not None}, retrieve={retrieve_file_func is not None}, list={list_files_func is not None}, propose={propose_code_change_func is not None}")
        
        # Compaction settings
        self._compaction_interval = compaction_interval
        self._overlap_size = overlap_size
        
        self._initialized = False
        ai_logger.debug("MultiAgentSystem constructor completed")
    
    def initialize(self) -> App:
        """
        Initialize all agents and return the App with compaction enabled.
        
        Returns:
            The App object wrapping the orchestrator with context compaction
        """
        if self._initialized:
            ai_logger.debug("MultiAgentSystem already initialized, returning existing App")
            return self._app
        
        ai_logger.debug("Starting MultiAgentSystem initialization sequence...")
        
        try:
            # Step 1: Register all function tools FIRST
            ai_logger.debug("[Step 1/5] Registering function tools...")
            self._register_function_tools()
            
            ai_logger.debug("[Step 1.5/5] Registering MCP tools...")
            self._register_mcp_tools()

            # Step 2: Create specialized sub-agents
            ai_logger.debug("[Step 2/5] Creating answering agent...")
            self._create_answering_agent()
            
            ai_logger.debug("[Step 3/6] Creating feature generation agent...")
            self._create_feature_agent()
            
            ai_logger.debug("[Step 4/6] Creating search agent...")
            self._create_web_search_agent()
            
            # Step 5: Register sub-agents as tools
            ai_logger.debug("[Step 5/6] Registering sub-agents as tools...")
            self._register_agent_tools()
            
            # Step 6: Create orchestrator with all registered tools
            ai_logger.debug("[Step 6/6] Creating orchestrator agent...")
            self._create_orchestrator()
            
            # Step 5: Create App with EventsCompactionConfig
            ai_logger.debug("Creating App with EventsCompactionConfig...")
            self._app = App(
                name=settings.APP_NAME,
                root_agent=self._orchestrator,
                events_compaction_config=EventsCompactionConfig(
                    compaction_interval=self._compaction_interval,
                    overlap_size=self._overlap_size
                )
            )
            
            self._initialized = True
            ai_logger.debug(
                f"MultiAgentSystem initialized successfully with compaction "
                f"(interval={self._compaction_interval}, overlap={self._overlap_size})"
            )
            
            return self._app
            
        except Exception as e:
            ai_logger.error(f"Failed to initialize MultiAgentSystem: {str(e)}", exc_info=True)
            raise
    
    def _register_function_tools(self):
        """Register all function-based tools."""
        ai_logger.debug("Registering function tools...")
        tools_registered = 0
        
        # Register search_index tool
        if self._search_tool_func:
            try:
                self._tool_registry.register_function(
                    name="search_index",
                    func=self._search_tool_func,
                    requires_confirmation=False
                )
                ai_logger.debug("Registered search_index tool")
                tools_registered += 1
            except Exception as e:
                ai_logger.error(f"Failed to register search_index tool: {str(e)}", exc_info=True)
                raise
        else:
            ai_logger.warning("search_tool_func not provided, search_index tool will not be available")
        
        # Register retrieve_code_file tool
        if self._retrieve_file_func:
            try:
                self._tool_registry.register_function(
                    name="retrieve_code_file",
                    func=self._retrieve_file_func,
                    requires_confirmation=False
                )
                ai_logger.debug("Registered retrieve_code_file tool")
                tools_registered += 1
            except Exception as e:
                ai_logger.error(f"Failed to register retrieve_code_file tool: {str(e)}", exc_info=True)
                raise
        else:
            ai_logger.warning("retrieve_file_func not provided, retrieve_code_file tool will not be available")
        
        # Register get_indexed_files tool
        if self._list_files_func:
            try:
                self._tool_registry.register_function(
                    name="get_indexed_files",
                    func=self._list_files_func,
                    requires_confirmation=False
                )
                ai_logger.debug("Registered get_indexed_files tool")
                tools_registered += 1
            except Exception as e:
                ai_logger.error(f"Failed to register get_indexed_files tool: {str(e)}", exc_info=True)
                raise
        else:
            ai_logger.warning("list_files_func not provided, get_indexed_files tool will not be available")
        
        # Register propose_code_change tool
        if self._propose_code_change_func:
            try:
                self._tool_registry.register_function(
                    name="propose_code_change",
                    func=self._propose_code_change_func,
                    requires_confirmation=False
                )
                ai_logger.debug("Registered propose_code_change tool")
                tools_registered += 1
            except Exception as e:
                ai_logger.error(f"Failed to register propose_code_change tool: {str(e)}", exc_info=True)
                raise
        else:
            ai_logger.warning("propose_code_change_func not provided, propose_code_change tool will not be available")
        
        ai_logger.debug(f"Function tools registration complete: {tools_registered} tools registered")
    
    def _register_mcp_tools(self):
        """
        Register MCP (Model Context Protocol) toolsets.
        """
        ai_logger.debug("MCP tools registration called (currently no MCP tools configured)")
        
        try:
            ms_learn_mcp = _microsoft_learn_mcp_toolset()
            self._tool_registry.register_mcp_tools("microsoft_learn_mcp", ms_learn_mcp)
            ai_logger.debug("Registered Microsoft Learn MCP toolset")
        except Exception as e:
            ai_logger.error(f"Failed to register Microsoft Learn MCP: {str(e)}", exc_info=True)
        
        ai_logger.debug("MCP tools registration complete")


    def _create_answering_agent(self):
        """Create the Answering Agent for code explanation queries."""
        answering_prompt = prompt_config.get("QUERY_ANSWERING_PROMPT", "")
        
        self._answering_agent = self._agent_manager.create(
            name="answering_agent",
            model=settings.FLASH_MODEL,
            instruction=answering_prompt + "\n\n" + PROMPT_GUIDELINES,
            description=(
                "Answers questions about the codebase. Use this agent when the user "
                "wants to understand how existing code works, what a module does, "
                "or needs explanation of architecture and design patterns. "
                "Pass the user's question along with relevant repository context."
            ),
            tools=[]  # Answering agent has no sub-tools
        )
        
        ai_logger.info("Answering agent created")
    
    def _create_feature_agent(self):
        """Create the Feature Generation Agent for code generation."""
        feature_prompt = prompt_config.get("FEATURE_GENERATION_PROMPT", "")
        
        self._feature_agent = self._agent_manager.create(
            name="feature_generation_agent",
            model=settings.ANALYSIS_MODEL,
            instruction=feature_prompt + "\n\n" + PROMPT_GUIDELINES,
            description=(
                "Generates new code and features. Use this agent when the user "
                "wants to add new functionality, modify existing code, or implement "
                "new features. Pass the feature request along with relevant codebase context."
            ),
            tools=[]
        )
        
        ai_logger.info("Feature generation agent created")
    
    def _create_web_search_agent(self):
        """Create the Search Agent for web searches."""
        web_search_prompt = prompt_config.get("WEB_SEARCH_AGENT", "You are Web Search Agent")
        search_prompt = (
            web_search_prompt + "\n\n" + PROMPT_GUIDELINES)
        
        self._web_search_agent = self._agent_manager.create(
            name="web_search_agent",
            model=settings.FLASH_MODEL,
            instruction=search_prompt,
            description=(
                "Searches the web for information. Use this agent when you need "
                "current information about libraries, documentation, best practices, "
                "or solutions that are not in the repository. Pass the search query."
            ),
            tools=[google_search]
        )
        
        ai_logger.info("Search agent created")
    
    def _register_agent_tools(self):
        """Register sub-agents as AgentTools for the orchestrator."""
        ai_logger.debug("Registering sub-agents as tools...")
        
        # Register answering agent
        if self._answering_agent:
            try:
                self._tool_registry.register_agent_as_tool(
                    name="answering_agent",
                    agent=self._answering_agent
                )
                ai_logger.debug("Registered answering_agent as AgentTool")
            except Exception as e:
                ai_logger.error(f"Failed to register answering_agent as tool: {str(e)}", exc_info=True)
                raise
        else:
            ai_logger.warning("answering_agent is None, cannot register as tool")
        
        # Register feature generation agent
        if self._feature_agent:
            try:
                self._tool_registry.register_agent_as_tool(
                    name="feature_generation_agent",
                    agent=self._feature_agent
                )
                ai_logger.debug("Registered feature_generation_agent as AgentTool")
            except Exception as e:
                ai_logger.error(f"Failed to register feature_generation_agent as tool: {str(e)}", exc_info=True)
                raise
        else:
            ai_logger.warning("feature_agent is None, cannot register as tool")
        
        # Register search agent
        if self._web_search_agent:
            try:
                self._tool_registry.register_agent_as_tool(
                    name="web_search_agent",
                    agent=self._web_search_agent
                )
                ai_logger.debug("Registered search_agent as AgentTool")
            except Exception as e:
                ai_logger.error(f"Failed to register search_agent as tool: {str(e)}", exc_info=True)
                raise
        else:
            ai_logger.warning("search_agent is None, cannot register as tool")
        
        ai_logger.debug("Sub-agent tools registration complete")
    
    def _create_orchestrator(self):
        """Create the Orchestrator agent with all registered tools."""
        ai_logger.debug("Creating orchestrator agent...")
        
        orchestrator_prompt = prompt_config.get("ORCHESTRATOR_PROMPT", "")
        if not orchestrator_prompt:
            ai_logger.warning("ORCHESTRATOR_PROMPT is empty or not found in config")
        else:
            ai_logger.debug(f"Loaded orchestrator prompt (length={len(orchestrator_prompt)})")
        
        all_tools = self._tool_registry.get_all()
        tool_names = self._tool_registry.list_names()
        ai_logger.debug(f"Orchestrator will have {len(all_tools)} tools: {tool_names}")
        
        try:
            self._orchestrator = self._agent_manager.create(
                name="orchestrator",
                model=settings.ANALYSIS_MODEL,
                instruction=orchestrator_prompt + "\n\n" + PROMPT_GUIDELINES,
                description="Main orchestrator that routes queries to specialized agents",
                tools=all_tools
            )
            ai_logger.debug(f"Orchestrator agent created with model={settings.ANALYSIS_MODEL}")
        except Exception as e:
            ai_logger.error(f"Failed to create orchestrator agent: {str(e)}", exc_info=True)
            raise
    
    def get_orchestrator(self) -> LlmAgent:
        """Get the orchestrator agent."""
        if not self._initialized:
            ai_logger.debug("get_orchestrator called but not initialized, initializing now...")
            self.initialize()
        return self._orchestrator
    
    def get_app(self) -> App:
        """Get the ADK App object with compaction enabled."""
        if not self._initialized:
            ai_logger.debug("get_app called but not initialized, initializing now...")
            return self.initialize()
        return self._app
    
    def get_answering_agent(self) -> LlmAgent:
        """Get the answering agent directly (for testing)."""
        ai_logger.debug("Retrieving answering agent directly")
        return self._answering_agent
    
    def get_feature_agent(self) -> LlmAgent:
        """Get the feature generation agent directly (for testing)."""
        ai_logger.debug("Retrieving feature generation agent directly")
        return self._feature_agent
    
    def get_tool_registry(self) -> ToolRegistry:
        """Get the tool registry for inspection."""
        ai_logger.debug("Retrieving tool registry")
        return self._tool_registry

    def get_web_search_agent(self) -> LlmAgent:
        """Get the web search agent directly (for testing)."""
        ai_logger.debug("Retrieving web search agent directly")
        return self._web_search_agent
