from sqlalchemy import update, select, true, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Chat


class ChatRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, chat_id: int, title: str | None) -> Chat:
        chat = Chat()

        chat.id = chat_id
        chat.title = title

        self.session.add(chat)
        await self.session.commit()

        return chat

    async def update(self, chat: Chat, **kwargs) -> Chat:
        for k, v in kwargs.items():
            setattr(chat, k, v)

        self.session.add(chat)
        await self.session.commit()

        return chat

    async def update_by_id(self, chat_id: int, **kwargs) -> None:
        await self.session.execute(update(Chat).values(**kwargs).filter(Chat.id == chat_id))
        await self.session.commit()

    async def get(self, chat_id: int) -> Chat:
        return await self.session.scalar(select(Chat).filter(Chat.id == chat_id))

    async def get_active(self) -> Sequence[int]:
        return (await self.session.scalars(select(Chat.id).filter(Chat.is_active == true()))).all()
