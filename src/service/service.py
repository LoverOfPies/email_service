from src.database.postgres import SessionManager


class Service:

    def __init__(self, session_manager: SessionManager, rabbit):
        self.session_manager = session_manager
        self.rabbit = rabbit

    async def run(self):
        while True:
            # Read from rabbit
            async with self.session_manager() as session:
                ...
