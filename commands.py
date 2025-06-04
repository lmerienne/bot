import os
from user import UserManager
from telegram.ext import ContextTypes
from telegram import Update
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
CHAT_ID = os.getenv("CHAT_ID")
THREAD_ID = os.getenv("THREAD_ID")
THREAD_ID = int(THREAD_ID) if THREAD_ID is not None else None

def restricted_to_thread(func):
    async def wrapper(update, context, *args, **kwargs):
        chat_id = update.effective_chat.id
        thread_id = getattr(update.message, 'message_thread_id', None)
        if str(chat_id) != str(CHAT_ID) or (THREAD_ID is not None and thread_id != THREAD_ID):
            logger.warning(f"Accès refusé pour {update.effective_user.username} dans {chat_id}, topic {thread_id}")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper



# Commandes telegram
@restricted_to_thread
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello!")

@restricted_to_thread
async def get_chat_id(update: Update, _: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = (f"Ton Chat ID est : {chat_id}\n"
            f"User ID : {user_id}\n"
            f"Thread ID: {getattr(update.message, 'message_thread_id', None)}")
    logger.warning(text)
    await update.message.reply_text(text)

@restricted_to_thread
async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage : /link <github_username>")
        return

    github_username = context.args[0]
    telegram_username = update.message.from_user.username

    try:
        UserManager.add_user(github_username, telegram_username)
        await update.message.reply_text(f"Utilisateur {github_username} lié à @{telegram_username}")
    except ValueError as e:
        await update.message.reply_text(str(e))
    except Exception as e:
        await update.message.reply_text(f"Erreur : {str(e)}")

@restricted_to_thread    
async def unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage : /unlink <github_username>")
        return

    github_username = context.args[0]

    try:
        UserManager.remove_user(github_username)
        await update.message.reply_text(f"Utilisateur {github_username} délié")
    except Warning as e:
        await update.message.reply_text(str(e))
    except Exception as e:
        await update.message.reply_text(f"Erreur : {str(e)}")