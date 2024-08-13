import os

from dotenv import load_dotenv

load_dotenv()
class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or ""


CONF = Config()
