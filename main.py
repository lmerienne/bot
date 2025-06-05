# main.py
import os
from contextlib import asynccontextmanager
from http import HTTPStatus
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException
from telegram import Update
from telegram.ext import Application, CommandHandler
import uvicorn
import logging
import hmac

from commands import start, get_chat_id, link, unlink

from webhooks import receive_github_webhook, process_telegram_update

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_DOMAIN = os.getenv("WEBHOOK_DOMAIN")
GITHUB_SECRET = os.getenv("GITHUB_SECRET")
CHAT_ID = os.getenv("CHAT_ID")
THREAD_ID = os.getenv("THREAD_ID")
THREAD_ID = int(THREAD_ID) if THREAD_ID is not None else None

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN non défini dans .env")
if not WEBHOOK_DOMAIN:
    raise ValueError("WEBHOOK_DOMAIN non défini dans .env")
if not GITHUB_SECRET:
    raise ValueError("GITHUB_SECRET non défini dans .env")
if not CHAT_ID:
    raise ValueError("CHAT_ID non défini dans .env")
if not THREAD_ID:
    raise ValueError("THREAD_ID non défini dans .env")

logger.info(f"Token Telegram : {TELEGRAM_BOT_TOKEN}")
logger.info(f"Webhook URL : {WEBHOOK_DOMAIN}")
logger.info(f"Chat ID : {CHAT_ID}")
logger.info(f"Thread ID : {THREAD_ID}")

# Création du bot telegram
tg_bot = (
    Application.builder()
    .token(TELEGRAM_BOT_TOKEN)
    .updater(None)
    .build()
)

# Gestion du cycle de vie du bot dans l'app FastAPI
@asynccontextmanager
async def lifespan(_: FastAPI):
    webhook_url = f"{WEBHOOK_DOMAIN}/telegram"
    logger.info(f"Configuration du webhook : {webhook_url}")
    await tg_bot.bot.setWebhook(url=webhook_url)
    async with tg_bot:
        await tg_bot.start()
        logger.info("Bot Telegram démarré")
        yield
        await tg_bot.stop()
        logger.info("Bot Telegram arrêté")

app = FastAPI(lifespan=lifespan)

@app.post("/telegram")
async def telegram_webhook_endpoint(request: Request):
    return await process_telegram_update(request, tg_bot)

@app.post("/webhook")
async def github_webhook_endpoint(request: Request):
    return await receive_github_webhook(request, tg_bot)

# Ajout des commandes au bot telegram
tg_bot.add_handler(CommandHandler("start", start))
tg_bot.add_handler(CommandHandler("get_chat_id", get_chat_id))
tg_bot.add_handler(CommandHandler("link", link))
tg_bot.add_handler(CommandHandler("unlink", unlink))

# Démarre le serveur FastAPI
if __name__ == "__main__":
    logger.info("Démarrage du serveur FastAPI")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )