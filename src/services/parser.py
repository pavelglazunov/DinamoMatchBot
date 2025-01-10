import asyncio
import datetime
import logging
from dataclasses import dataclass
from typing import Sequence

import aiohttp.client_exceptions
from aiohttp import ClientSession
from bs4 import BeautifulSoup

MONTHS_DECODER = {
    "янв": 1,
    "фев": 2,
    "мар": 3,
    "апр": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "авг": 8,
    "сен": 9,
    "окт": 10,
    "ноя": 11,
    "дек": 12,
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
    url = "https://fcdm.ru/fixtures/dynamo/calendar/"

    def __init__(self):
        self.matches = set()

    async def get_page(self, month: int, year: int) -> (str, int, int):
        try:
            async with ClientSession() as session:
                async with session.get(
                        url=self.url,
                        params={"year": year, "month": month},
                ) as response:
                    response.raise_for_status()
                    return await response.text(), month, year
        except aiohttp.client_exceptions.ClientConnectorError:
            return "", month, year
        except aiohttp.client_exceptions.ClientResponseError:
            return "", month, year

    async def parse(self):

        today = datetime.date.today()
        current_month = today.month
        current_year = today.year

        funcs = [self.get_page(month, current_year) for month in range(current_month, 13)]

        pages_content = await asyncio.gather(*funcs)
        pool = [(*cnt, 0) for cnt in pages_content]
        limit = 10
        while pool:
            content, month, year, retries = pool.pop(0)
            if content:
                await self.parse_matches(content)
                continue
            if retries < limit:
                pool.append((*(await self.get_page(month, year)), retries + 1))
            else:
                logging.error(f"can't fetch {month} month {year} year after {limit} retries")

    async def parse_matches(self, html: str):
        soup = BeautifulSoup(html)

        matches = soup.find_all("div", {
            "class": "js-match-calendar-card",
        })
        for match_html in matches:
            content = match_html.find_next("div", {"class": "schedule-row__wrap"})

            location = content.find_next("div", {"class": "schedule-row__location"})
            teams = content.find_next(
                "div",
                {"class": "schedule-row__teams"},
            ).find_all(
                "div",
                {"class": "schedule-row__team"},
            )

            date = location.find_next("div", {"class": "schedule-row__time"}).text
            team_names = []
            for team in teams:
                name = team.find_next("div", {"class": "schedule-row__team-name"}).text
                team_names.append(name)

            if len(team_names) != 2:
                continue

            if "-" in date or ":" not in date:
                continue
            try:
                match = Match(
                    team1=team_names[0],
                    team2=team_names[1],
                    string_time=date,
                    time=self.formalize_datetime(date),
                )
            except:
                continue

            self.matches.add(match)

    @staticmethod
    def formalize_datetime(match_datetime: str) -> datetime.datetime:
        match_datetime = match_datetime.replace(".", "")
        match_date_str, _, match_time_str = match_datetime.rpartition(" ")

        match_day, match_month = match_date_str.strip().split()
        mathc_hour, match_minute = match_time_str.split(":")

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
