"""
MCP (Model Context Protocol) Initialization Module

This module provides utilities to initialize and manage MCP toolsets
for Google ADK agents. It supports both SSE/HTTP-based and Stdio-based
MCP servers.

Supported MCP Types:
- SSE (Server-Sent Events): For remote HTTP-based MCP servers
- STDIO: For local process-based MCP servers (e.g., npx-based)
- STREAMABLE_HTTP: For HTTP-based streamable MCP servers (new MCP protocol)

Usage:
    from app.services.agents.mcp.initialize_mcp import initialize_mcp_toolset, MCPConfig
    
    # For SSE-based MCP
    config = MCPConfig(
        mcp_type="sse",
        url="http://localhost:8080/mcp",
        headers={"Authorization": "Bearer token"}
    )
    toolset = await initialize_mcp_toolset(config)
    
    # For Stdio-based MCP (e.g., npx packages)
    config = MCPConfig(
        mcp_type="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/folder"]
    )
    toolset = await initialize_mcp_toolset(config)
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field
import logging

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
    SseConnectionParams,
    StreamableHTTPConnectionParams,
)
from mcp import StdioServerParameters

logger = logging.getLogger(__name__)


class MCPType(str, Enum):
    """Supported MCP connection types."""
    SSE = "sse"                     # Server-Sent Events (HTTP-based)
    STDIO = "stdio"                 # Standard I/O (local process)
    STREAMABLE_HTTP = "streamable_http"  # Streamable HTTP (new MCP protocol)


@dataclass
class MCPConfig:
    """
    Configuration for initializing an MCP connection.
    
    Attributes:
        mcp_type: Type of MCP connection (sse, stdio, or streamable_http)
        name: Optional friendly name for the MCP toolset
        
        # For SSE/HTTP-based MCPs:
        url: The URL of the MCP server endpoint
        headers: Optional HTTP headers (e.g., for authentication)
        timeout: Connection timeout in seconds
        
        # For Stdio-based MCPs:
        command: The command to execute (e.g., 'npx', 'python')
        args: Arguments for the command
        env: Optional environment variables for the process
        cwd: Optional working directory for the process
        
        # Common options:
        tool_filter: Optional list of tool names to expose (None = all tools)
    """
    mcp_type: MCPType
    name: Optional[str] = None
    
    # SSE/HTTP configuration
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    timeout: float = 30.0
    
    # Stdio configuration
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    
    # Common options
    tool_filter: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate configuration based on MCP type."""
        if isinstance(self.mcp_type, str):
            self.mcp_type = MCPType(self.mcp_type.lower())
        
        if self.mcp_type in (MCPType.SSE, MCPType.STREAMABLE_HTTP):
            if not self.url:
                raise ValueError(f"{self.mcp_type.value} MCP requires 'url' parameter")
        elif self.mcp_type == MCPType.STDIO:
            if not self.command:
                raise ValueError("STDIO MCP requires 'command' parameter")
            if self.args is None:
                self.args = []


def create_sse_connection_params(config: MCPConfig) -> SseConnectionParams:
    """
    Create SSE connection parameters from config.
    
    Args:
        config: MCPConfig with SSE settings
        
    Returns:
        SseConnectionParams for McpToolset
    """
    return SseConnectionParams(
        url=config.url,
        headers=config.headers or {},
        timeout=config.timeout,
    )


def create_streamable_http_connection_params(config: MCPConfig) -> StreamableHTTPConnectionParams:
    """
    Create Streamable HTTP connection parameters from config.
    
    Args:
        config: MCPConfig with Streamable HTTP settings
        
    Returns:
        StreamableHTTPConnectionParams for McpToolset
    """
    return StreamableHTTPConnectionParams(
        url=config.url,
        headers=config.headers or {},
        timeout=config.timeout,
    )


def create_stdio_connection_params(config: MCPConfig) -> StdioConnectionParams:
    """
    Create Stdio connection parameters from config.
    
    Args:
        config: MCPConfig with Stdio settings
        
    Returns:
        StdioConnectionParams for McpToolset
    """
    server_params = StdioServerParameters(
        command=config.command,
        args=config.args or [],
        env=config.env,
        cwd=config.cwd,
    )
    return StdioConnectionParams(server_params=server_params)


def create_mcp_toolset(config: MCPConfig) -> McpToolset:
    """
    Create an MCP toolset from configuration.
    
    This is a synchronous factory function that creates the McpToolset.
    The actual connection to the MCP server happens asynchronously when
    the toolset is used.
    
    Args:
        config: MCPConfig specifying the MCP connection details
        
    Returns:
        McpToolset configured for the specified MCP server
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Validate config
    config.__post_init__()
    
    # Create connection params based on type
    if config.mcp_type == MCPType.SSE:
        connection_params = create_sse_connection_params(config)
        logger.info(f"Creating SSE MCP toolset for: {config.url}")
    elif config.mcp_type == MCPType.STREAMABLE_HTTP:
        connection_params = create_streamable_http_connection_params(config)
        logger.info(f"Creating Streamable HTTP MCP toolset for: {config.url}")
    elif config.mcp_type == MCPType.STDIO:
        connection_params = create_stdio_connection_params(config)
        logger.info(f"Creating Stdio MCP toolset with command: {config.command}")
    else:
        raise ValueError(f"Unsupported MCP type: {config.mcp_type}")
    
    # Create toolset with optional tool filter
    toolset_kwargs = {
        "connection_params": connection_params,
    }
    
    if config.tool_filter:
        toolset_kwargs["tool_filter"] = config.tool_filter
        logger.info(f"Tool filter applied: {config.tool_filter}")
    
    return McpToolset(**toolset_kwargs)


async def initialize_mcp_toolset(config: MCPConfig) -> McpToolset:
    """
    Initialize an MCP toolset asynchronously.
    
    This is the main entry point for creating MCP toolsets. Use this
    when you need to ensure the MCP connection is established before
    using the toolset.
    
    Args:
        config: MCPConfig specifying the MCP connection details
        
    Returns:
        McpToolset ready for use with ADK agents
        
    Example:
        ```python
        config = MCPConfig(
            mcp_type="sse",
            url="http://localhost:8080/mcp"
        )
        toolset = await initialize_mcp_toolset(config)
        
        agent = LlmAgent(
            model='gemini-2.0-flash',
            name='my_agent',
            instruction='Help the user',
            tools=[toolset]
        )
        ```
    """
    toolset = create_mcp_toolset(config)
    logger.info(f"MCP toolset initialized: {config.name or config.mcp_type.value}")
    return toolset


async def close_mcp_toolset(toolset: McpToolset) -> None:
    """
    Properly close and cleanup an MCP toolset.
    
    Call this when you're done using the MCP toolset to ensure
    proper cleanup of resources and connections.
    
    Args:
        toolset: The McpToolset to close
    """
    try:
        await toolset.close()
        logger.info("MCP toolset closed successfully")
    except Exception as e:
        logger.error(f"Error closing MCP toolset: {e}")
        raise


# Convenience functions for common MCP types
def create_sse_mcp_toolset(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    tool_filter: Optional[List[str]] = None,
    timeout: float = 30.0,
    name: Optional[str] = None,
) -> McpToolset:
    """
    Create an SSE-based MCP toolset.
    
    Args:
        url: The URL of the SSE MCP server
        headers: Optional HTTP headers for authentication
        tool_filter: Optional list of tools to expose
        timeout: Connection timeout in seconds
        name: Optional friendly name
        
    Returns:
        McpToolset configured for SSE connection
    """
    config = MCPConfig(
        mcp_type=MCPType.SSE,
        url=url,
        headers=headers,
        tool_filter=tool_filter,
        timeout=timeout,
        name=name,
    )
    return create_mcp_toolset(config)


def create_streamable_http_mcp_toolset(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    tool_filter: Optional[List[str]] = None,
    timeout: float = 30.0,
    name: Optional[str] = None,
) -> McpToolset:
    """
    Create a Streamable HTTP-based MCP toolset.
    
    Args:
        url: The URL of the Streamable HTTP MCP server
        headers: Optional HTTP headers for authentication
        tool_filter: Optional list of tools to expose
        timeout: Connection timeout in seconds
        name: Optional friendly name
        
    Returns:
        McpToolset configured for Streamable HTTP connection
    """
    config = MCPConfig(
        mcp_type=MCPType.STREAMABLE_HTTP,
        url=url,
        headers=headers,
        tool_filter=tool_filter,
        timeout=timeout,
        name=name,
    )
    return create_mcp_toolset(config)


def create_stdio_mcp_toolset(
    command: str,
    args: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None,
    tool_filter: Optional[List[str]] = None,
    name: Optional[str] = None,
) -> McpToolset:
    """
    Create a Stdio-based MCP toolset for local MCP servers.
    
    Args:
        command: Command to execute (e.g., 'npx', 'python')
        args: Arguments for the command
        env: Optional environment variables
        cwd: Optional working directory
        tool_filter: Optional list of tools to expose
        name: Optional friendly name
        
    Returns:
        McpToolset configured for Stdio connection
        
    Example:
        ```python
        # For filesystem MCP server via npx
        toolset = create_stdio_mcp_toolset(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/folder"]
        )
        ```
    """
    config = MCPConfig(
        mcp_type=MCPType.STDIO,
        command=command,
        args=args,
        env=env,
        cwd=cwd,
        tool_filter=tool_filter,
        name=name,
    )
    return create_mcp_toolset(config)

