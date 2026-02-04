import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

REMNAWAVE_BASE_URL = os.getenv("REMNAWAVE_BASE_URL")
REMNAWAVE_TOKEN = os.getenv("REMNAWAVE_TOKEN")
EGAMES_COOKIE = os.getenv("EGAMES_COOKIE")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")

if not REMNAWAVE_BASE_URL:
    raise ValueError("REMNAWAVE_BASE_URL is not set in .env")

if not REMNAWAVE_TOKEN:
    raise ValueError("REMNAWAVE_TOKEN is not set in .env")

if not EGAMES_COOKIE:
    raise ValueError("EGAMES_COOKIE is not set in .env")
