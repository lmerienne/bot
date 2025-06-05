# webhooks.py
import os
import hmac
import hashlib
import logging
from http import HTTPStatus
from fastapi import Request, Response, HTTPException
from telegram import Update
from telegram.ext import Application 

from event import EVENT_CLASSES
from filter import MessageFilter

logger = logging.getLogger(__name__)

GITHUB_SECRET = os.getenv("GITHUB_SECRET")
CHAT_ID = os.getenv("CHAT_ID")
THREAD_ID = os.getenv("THREAD_ID")

# Vérifie la signature envoyée par github
def is_valid_github_signature(signature: str, raw_body: bytes) -> bool:
    if not signature or not signature.startswith("sha256="):
        return False
    signature_hash = signature.split("=")[1]
    mac = hmac.new(GITHUB_SECRET.encode('utf-8'), raw_body, hashlib.sha256)
    computed_hash = mac.hexdigest()
    return hmac.compare_digest(computed_hash, signature_hash)



# Endpoint pour les webhooks telegram
async def process_telegram_update(request: Request, tg_bot: Application):
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
async def receive_github_webhook(request: Request, tg_bot: Application):
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
