from aiogram import Router, types
from aiogram.filters import CommandStart
from sqlalchemy.exc import IntegrityError

from src.repo import DB

router = Router()


@router.message(CommandStart())
async def start(message: types.Message, db: DB):
    try:
        await db.chat.create(message.chat.id, message.chat.title)
    except IntegrityError:
        pass

    await message.answer("Привет!\n\n"
                         "Я бот, который может напоминать о матчах Динамо, а во время самих матче "
                         "болеть за команду\n\n"
                         "Сейчас я включен, а это значить, что я буду присылать напоминания и "
                         "кричалки динамо. Чтобы меня выключить, можешь использовать команду /off"
                         ", но потом не забудь меня снова включить при помощи /on\n\n"
                         "ДИНОМО ВПЕРЕД!")
