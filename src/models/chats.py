from src.models.base import Base
from sqlalchemy import Column, BigInteger, Boolean, String


class Chat(Base):
    __tablename__ = "chats"

    id = Column(BigInteger, primary_key=True)
    title = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
