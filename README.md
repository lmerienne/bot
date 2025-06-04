# Telegram GitHub Bot

Bot Telegram qui relaie les notifications de un ou plusieurs dépôts GitHub dans un thread dédié dans un supergroupe Telegram. 
Basé sur FastAPI et python-telegram-bot

## Fonctionnalités

- Relais des évènements GitHub (`push`, `pull_request`) dans un thread spécifique d'un supergroupe Telegram.
- Commandes `/link`et `/unlink`pour associer son nom d'utilisateur GitHub à son nom d'utilisateur Telegram.

## Installation 
1. **Cloner le repo**
    ```bash
    git clone https://github.com/lmerienne/bot.git
    cd bot
    ```

2. **Setup de l'environnement virtuel**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Installation des dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup des variables d'environnement**
   
   Créer un fichier .env à la racine du projet et le remplir tel que :
   ```properties
    TELEGRAM_BOT_TOKEN=<le_token_du_bot_telegram>
    GITHUB_SECRET=<le-secret_choisi-pour-les-webhooks>
    CHAT_ID=<chat_id du supergroupe>
    THREAD_ID=<id du thread dédié>
    WEBHOOK_DOMAIN=<url publique du serveur>
    ```

- Pour obtenir `CHAT_ID` et `THREAD_ID`, utilise la commande `/get_chat_id` dans le thread voulu.

## Lancement du bot

- **Lancer le serveur FastAPI :**
  ```bash
  python3 main.py
  ```

- **Exposer le serveur à internet**

- **Configurer les webhooks dans les dépôts GitHub :**
  - URL du webhook : `https://<url-de-ton-serveur>/webhook`
  - Content type : `application/json`
  - Secret : même valeur que le `GITHUB_SECRET`dans le `.env`
  - Activer tous les événements

- **Ajouter le bot Telegram et récupérer les ID via la commande `/get_chat_id`**