from google.adk.memory import InMemoryMemoryService

from app.utils.logget_setup import ai_logger


class MemoryStore:
    """Singleton memory store for agent context."""
    _instance = None

    @classmethod
    def get(cls):
        """Get or create the memory service singleton."""
        if cls._instance is None:
            ai_logger.debug("Initializing InMemoryMemoryService singleton")
            cls._instance = InMemoryMemoryService()
            ai_logger.debug("MemoryStore initialized successfully")
        return cls._instance
