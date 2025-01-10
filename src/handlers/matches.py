from aiogram import Router, types
from aiogram.filters import Command

from src.repo import DB
from src.services.parser import DinamoParser

router = Router()


@router.message(Command("matches"))
async def set_activity_on(message: types.Message, dinamo: DinamoParser):
    content = "Ближайшие матчи:\n\n"

    for match in dinamo.matches:
        content += f"{match.string_time} | {match.team1} - {match.team2}\n"

    await message.answer(content)
