import os
from app.core.configs.app_config import settings
from app.services.agents.manager.agent_manager import AgentManager
from app.services.agents.manager.memory_manager import MemoryStore
from app.services.agents.manager.session_manager import SessionManager
from app.services.agents.manager.tool_manager import ToolRegistry

GOOGLE_API_KEY = settings.GOOGLE_API_KEY
GOOGLE_GENAI_USE_VERTEXAI = False

APP_NAME = "ReqioIQ"

agent_manager = AgentManager()
memory_store = MemoryStore()
session_manager = SessionManager()
tool_registry = ToolRegistry()