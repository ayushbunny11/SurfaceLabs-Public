from google.adk.memory import InMemoryMemoryService

class MemoryStore:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = InMemoryMemoryService()
        return cls._instance
