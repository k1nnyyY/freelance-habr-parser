import asyncio
import datetime
import logging
import signal
from contextlib import suppress
from os.path import join, dirname
from time import time, sleep
from multiprocessing import Process
from time import sleep

import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from peewee import *

from config import CONF

db = SqliteDatabase('sqlite.db')
db.connect()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=CONF.TELEGRAM_BOT_TOKEN)

dp = Dispatcher()


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    user_id = CharField(unique=True)


class Article(BaseModel):
    title = CharField()
    link = CharField(unique=True)
    price = CharField()
    sent = BooleanField(default=False)


db.create_tables([User, Article])


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    from_id = str(message.from_user.id)
    try:
        User.create(user_id=from_id)
        await message.answer("You " + from_id + " subscribed")
    except Exception:
        await message.answer("You " + from_id + " has been already subscribed")


async def parser(ioloop):
    url = 'https://freelance.habr.com/tasks?categories=development_backend%2Cdevelopment_bots%2Cdevelopment_other%2Cadmin%2Cdevelopment_frontend%2Cdevelopment_scripts%2Ctesting_sites%2Ccontent_specification%2Cmarketing_sales%2Cmarketing_research%2Cother_audit_analytics'

    print("Request: ", datetime.datetime.now())
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    articles = soup.findAll('article')
    articles_new = []
    for article in articles:
        title_element = article.find("div", class_="task__title")
        title_element_text = title_element.text
        link_element = title_element.find("a")
        link_element_href = link_element["href"]
        price_element_text = article.find("div", class_="task__price").text
        try:
            art = Article.create(link=link_element_href,
                                 title=title_element_text,
                                 price=price_element_text,
                                 sent=True)
            articles_new.append(art)
        except:
            continue

    if len(articles_new) > 0:
        tg_str = ""
        for new in articles_new:
            tg_str += (f'{new.title}\n'
                       f'Link: https://freelance.habr.com{new.link}\n'
                       f'Price: {new.price}\n\n')

        if tg_str != "":
            print(tg_str)

        users = User.select()
        for user in users:
            await bot.send_message(user.user_id, tg_str)

    await asyncio.sleep(30)
    await parser(ioloop)


async def main(ioloop):
    tasks = [ioloop.create_task(dp.start_polling(bot)), ioloop.create_task(parser(ioloop))]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    for pending_future in pending:
        pending_future.cancel()


if __name__ == "__main__":
    ioloop = asyncio.get_event_loop()
    ioloop.run_until_complete(main(ioloop))
    ioloop.close()
