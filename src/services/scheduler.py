import asyncio
import logging
import random
from asyncio import PriorityQueue
from datetime import datetime, time, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.repo import DB
from src.services.parser import DinamoParser, Match
from config.dinamo import DINAMO_SUPPORTS


async def mailing(bot: Bot, content: str, chats: list[int]):
    retries = PriorityQueue()
    for chat_id in chats:
        await retries.put((0, chat_id))

    while not retries.empty():
        timeout, chat = await retries.get()

        await asyncio.sleep(timeout)
        try:
            await bot.send_message(chat, content)
        except TelegramRetryAfter as error:
            await retries.put((error.retry_after, chat))
        except (TelegramBadRequest, TelegramForbiddenError):
            continue


async def match_support(bot: Bot, chat_id: int, match: Match, session_maker: async_sessionmaker):
    await mailing(bot, f"Начинается матч {match.team1} - {match.team2}", [chat_id])
    total_seconds = 0

    while total_seconds < 3600 * 2:
        waiting_seconds = random.randint(50, 120)
        total_seconds += waiting_seconds
        async with session_maker() as session:
            db = DB(session)

            chat = await db.chat.get(chat_id)
            if not chat.is_active:
                await asyncio.sleep(waiting_seconds)
                continue

        message = random.choice(DINAMO_SUPPORTS)

        await mailing(bot, message, [chat_id])
        await asyncio.sleep(waiting_seconds)


async def run(bot: Bot, session_maker: async_sessionmaker, dinamo: DinamoParser):
    await dinamo.parse()
    await dinamo.drop_old()
    logging.info("parsed successful")
    dinamo.matches.add(Match(
        team1="Мотя",
        team2="Митя",
        string_time="8 янв. 19:00",
        time=datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=1),
    ))

    reparse_counter = 0

    while True:
        now = datetime.now().replace(second=0, microsecond=0)
        async with session_maker() as session:
            db = DB(session)

            chats = await db.chat.get_active()

        for match in dinamo.matches:
            delta = (match.time - now)
            for interval, message in zip(
                    (timedelta(days=1), timedelta(hours=1), timedelta(minutes=30),
                     timedelta(minutes=1)),
                    ("остался 1 день", "остался 1 час", "осталось 30 минут", "осталась 1 минута"),
            ):
                if delta == interval:
                    content = f"До матча {match.team1} - {match.team2} {message}"
                    asyncio.create_task(mailing(bot, content, chats))
            if not delta:
                for chat in chats:
                    asyncio.create_task(match_support(bot, chat, match, session_maker))

        reparse_counter += 1
        if reparse_counter == 60 * 24:
            await dinamo.parse()
            await dinamo.drop_old()

        await asyncio.sleep(60)
