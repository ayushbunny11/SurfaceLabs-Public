from google.adk.sessions import InMemorySessionService

class SessionManager:
    def __init__(self):
        self.service = InMemorySessionService()

    async def create(self, APP_NAME: str, user_id: str, session_id: str):
        """Create a new session. Raises error if session already exists."""
        session = await self.service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        return session
    
    async def get_or_create(self, APP_NAME: str, user_id: str, session_id: str):
        """Get existing session or create a new one if it doesn't exist."""
        # Try to get existing session first
        try:
            session = await self.service.get_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            if session:
                return session
        except Exception:
            pass  # Session doesn't exist, create a new one
        
        # Create new session
        session = await self.service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        return session

    def get_service(self):
        return self.service
