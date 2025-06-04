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

from event import EVENT_CLASSES
from filter import MessageFilter
from commands import start, get_chat_id, link, unlink

import hashlib

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

# Vérifie la signature envoyée par github
def is_valid_github_signature(signature: str, raw_body: bytes) -> bool:
    if not signature or not signature.startswith("sha256="):
        return False
    signature_hash = signature.split("=")[1]
    mac = hmac.new(GITHUB_SECRET.encode('utf-8'), raw_body, hashlib.sha256)
    computed_hash = mac.hexdigest()
    return hmac.compare_digest(computed_hash, signature_hash)



# Endpoint pour les webhooks telegram
@app.post("/telegram")
async def process_update(request: Request):
    logger.info("Requête Telegram reçue")
    try:
        message = await request.json()
        update = Update.de_json(data=message, bot=tg_bot.bot)
        if update:
            await tg_bot.process_update(update)
        return Response(status_code=HTTPStatus.OK)
    except Exception as e:
        logger.error(f"Erreur dans process_update : {str(e)}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    

# Endpoint pour les webhooks github
@app.post("/webhook")
async def receive_webhook(request: Request):
    logger.info("Requête webhook GitHub reçue")
    signature = request.headers.get("X-Hub-Signature-256")
    logger.debug(f"Signature : {signature}")
    if not signature:
        logger.error("Signature manquante")
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Signature manquante")

    raw_body = await request.body()
    logger.debug(f"Body : {raw_body[:100]}...")

    if not is_valid_github_signature(signature, raw_body):
        logger.error("Signature invalide")
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Signature invalide")

    event = request.headers.get("X-GitHub-Event")
    logger.info(f"Événement : {event}")
    if not event:
        logger.error("Événement manquant")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Événement manquant")

    try:
        data = await request.json()
        logger.debug(f"Données : {data}")

        if event == "ping":
            logger.info("Ping reçu")
            return {"message": "Webhook pingé avec succès"}

        message_filter = MessageFilter()
        if not message_filter.is_event_enabled(event, data):
            logger.info("Événement ignoré par les filtres")
            return {"message": "Événement ignoré par les filtres"}

        event_class = EVENT_CLASSES.get(event)
        if not event_class:
            logger.error("Événement non supporté")
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Événement non supporté")

        event = event_class(data)
        message = event.format_message()
        if not message:
            logger.error("Message vide")
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Message vide")

        logger.info(f"Envoi du message à CHAT_ID {CHAT_ID}: {message}")
        await tg_bot.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode="Markdown",
            message_thread_id=THREAD_ID
        )
        logger.info("Notification envoyée")
        return {"message": "Notification envoyée"}

    except Exception as e:
        logger.error(f"Erreur : {str(e)}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f"Erreur : {str(e)}")


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