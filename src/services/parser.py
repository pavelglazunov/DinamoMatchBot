import asyncio
import datetime
import logging
from dataclasses import dataclass
from typing import Sequence

import aiohttp.client_exceptions
from aiohttp import ClientSession
from bs4 import BeautifulSoup

MONTHS_DECODER = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


@dataclass
class Match:
    team1: str
    team2: str

    string_time: str
    time: datetime.datetime

    def __hash__(self):
        return hash("".join(sorted([self.team1, self.team2, str(self.time)])))


class DinamoParser:
    url = "https://dynamo.ru/games"

    def __init__(self):
        self.matches = set()

    async def get_page(self, month: int) -> (str, int, int):
        try:
            async with ClientSession() as session:
                async with session.get(self.url + f"#{month}-list") as response:
                    response.raise_for_status()
                    return await response.text(), month
        except aiohttp.client_exceptions.ClientConnectorError:
            return "", month
        except aiohttp.client_exceptions.ClientResponseError:
            return "", month

    async def parse(self):

        today = datetime.date.today()
        current_month = today.month

        funcs = [self.get_page(month) for month in range(current_month, 13)]

        pages_content = await asyncio.gather(*funcs)
        pool = [(*cnt, 0) for cnt in pages_content]
        limit = 10
        while pool:
            content, month, retries = pool.pop(0)
            if content:
                await self.parse_matches(content)
                continue
            if retries < limit:
                pool.append((*(await self.get_page(month)), retries + 1))
            else:
                logging.error(f"can't fetch {month} month after {limit} retries")

    async def parse_matches(self, html: str):
        soup = BeautifulSoup(html)

        matches = soup.find_all("div", {
            "class": "calendarthumb _state-base",
        })
        for match_html in matches:
            # content = match_html.find_next("div", {"class": "calendarthumb__body"})

            location = match_html.find_next("time", {"class": "calendarthumb__date-detail"})
            teams = match_html.find_next(
                "div",
                {"class": "calendarthumb__body"},
            ).find_all(
                "div",
                {"class": "calendarthumb__textbox"}
            )
            date = location.find_next("span", {"class": "calendarthumb__text-item"}).text
            time = location.find_next("span", {"class": "calendarthumb__text-item _sub"}).text

            flag = match_html.find_next(
                "div",
                {"class": "calendarthumb__body"},
            ).find_next(
                "span",
                {"class": "calendarthumb__body-additional"}
            )
            if not flag:
                continue

            # date = location.find_next("div", {"class": "schedule-row__time"}).text
            team_names = []
            for team in teams:
                name = team.find_next("div", {"class": "calendarthumb__textbox-content"}).text
                team_names.append(name)

            if len(team_names) != 2:
                continue

            try:
                match = Match(
                    team1=team_names[0],
                    team2=team_names[1],
                    string_time=date + " " + time,
                    time=self.formalize_datetime(date, time),
                )
            except Exception as e:
                continue

            self.matches.add(match)

    @staticmethod
    def formalize_datetime(match_date: str, mathc_time: str) -> datetime.datetime:
        match_day, match_month = match_date.strip().split("/")[0].split()
        mathc_hour, match_minute = mathc_time.split(":")

        today = datetime.date.today()
        return datetime.datetime(
            year=today.year,
            month=MONTHS_DECODER.get(match_month, 1),
            day=int(match_day),
            hour=int(mathc_hour),
            minute=int(match_minute),
            second=0,
            microsecond=0,
        )

    async def drop_old(self):
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        self.matches = set(filter(lambda m: m.time > yesterday, self.matches))

    # # for

# async def main():
#     p = DinamoParser()
#
#     await p.parse()
#     print(p.matches)
#
#
# asyncio.run(main())
