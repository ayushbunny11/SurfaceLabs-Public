from typing import List, Optional
from app.services.agents.mcp.initialize_mcp import create_streamable_http_mcp_toolset, McpToolset

def _microsoft_learn_mcp_toolset(
    tool_filter: Optional[List[str]] = None,
    timeout: float = 60.0,
) -> McpToolset:
    """
    Create an MCP toolset for Microsoft Learn documentation.
    
    Provides access to up-to-date content from Microsoft's official
    documentation via the Model Context Protocol.
    
    Args:
        tool_filter: Optional list of tools to expose (None = all tools)
        timeout: Connection timeout in seconds (default: 60s)
        
    Returns:
        McpToolset for Microsoft Learn documentation access
        
    Example:
        ```python
        # Create toolset for Microsoft Learn
        toolset = _microsoft_learn_mcp_toolset()
        
        # Use with ADK Agent
        agent = LlmAgent(
            model='gemini-2.0-flash',
            name='docs_assistant',
            instruction='Help users find Microsoft documentation',
            tools=[toolset]
        )
        ```
    """
    return create_streamable_http_mcp_toolset(
        url="https://learn.microsoft.com/api/mcp",
        tool_filter=tool_filter,
        timeout=timeout,
        name="microsoft_learn_mcp",
    )
