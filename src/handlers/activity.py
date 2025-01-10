from aiogram import Router, types
from aiogram.filters import Command

from src.repo import DB

router = Router()


@router.message(Command("on"))
async def set_activity_on(message: types.Message, db: DB):
    await db.chat.update_by_id(message.chat.id, is_active=True)
    await message.answer("Бот успешно включен")


@router.message(Command("off"))
async def set_activity_off(message: types.Message, db: DB):
    await db.chat.update_by_id(message.chat.id, is_active=False)
    await message.answer("Бот успешно выключен")

