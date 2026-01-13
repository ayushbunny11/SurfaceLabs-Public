from google.adk.sessions import InMemorySessionService

class SessionManager:
    def __init__(self):
        self.service = InMemorySessionService()

    async def create(self, APP_NAME: str, user_id: str, session_id: str):
        session = await self.service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        return session

    def get_service(self):
        return self.service
