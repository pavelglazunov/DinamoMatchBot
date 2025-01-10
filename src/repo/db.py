from sqlalchemy.ext.asyncio import AsyncSession

from src.repo.chat import ChatRepo


class DB:
    def __init__(self, session: AsyncSession):
        self.chat = ChatRepo(session)
