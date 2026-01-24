from google.adk.sessions import InMemorySessionService

from app.utils.logget_setup import ai_logger


class SessionManager:
    """Manages chat sessions for agent interactions."""
    
    def __init__(self):
        self.service = InMemorySessionService()
        ai_logger.debug("SessionManager initialized with InMemorySessionService")

    async def create(self, APP_NAME: str, user_id: str, session_id: str):
        """Create a new session. Raises error if session already exists."""
        ai_logger.debug(f"Creating new session: app={APP_NAME}, user={user_id}, session={session_id}")
        try:
            session = await self.service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            ai_logger.debug(f"Session created successfully: {session_id}")
            return session
        except Exception as e:
            ai_logger.error(f"Failed to create session {session_id}: {str(e)}", exc_info=True)
            raise
    
    async def get_or_create(self, APP_NAME: str, user_id: str, session_id: str):
        """Get existing session or create a new one if it doesn't exist."""
        ai_logger.debug(f"Get or create session: app={APP_NAME}, user={user_id}, session={session_id}")
        
        # Try to get existing session first
        try:
            session = await self.service.get_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            if session:
                ai_logger.debug(f"Found existing session: {session_id}")
                return session
        except Exception as e:
            ai_logger.debug(f"Session {session_id} not found, will create new one: {str(e)}")
        
        # Create new session
        try:
            session = await self.service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            ai_logger.debug(f"Created new session: {session_id}")
            return session
        except Exception as e:
            ai_logger.error(f"Failed to create session {session_id}: {str(e)}", exc_info=True)
            raise

    def get_service(self):
        """Return the underlying session service."""
        return self.service
