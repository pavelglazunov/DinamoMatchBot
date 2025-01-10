from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from config.config import Config
from src.services.parser import DinamoParser


class GetDinamoMiddleware(BaseMiddleware):
    def __init__(self, dinamo: DinamoParser):
        super().__init__()
        self.dinamo = dinamo

    async def __call__(
            self,
            handler: Callable[
                [TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        data["dinamo"] = self.dinamo

        return await handler(event, data)
