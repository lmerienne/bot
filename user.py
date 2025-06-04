import json
import os
import re
from typing import Dict

USERS_FILE = "users.json"

class UserManager:

    @staticmethod
    def load_users() -> Dict[str, str]:
        if not os.path.exists(USERS_FILE):
            with open(USERS_FILE, "w") as f:
                json.dump({}, f)
        
        with open(USERS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Erreur de lecture du fichier users")
                return {}
    
    @staticmethod
    def save_users(mapping: Dict[str, str]):
        with open(USERS_FILE, "w") as f :
            json.dump(mapping, f, indent=2)
    
    @staticmethod
    def add_user(github_username:str, telegram_username:str):
        if not re.match(r"^[A-Za-z0-9_]{1,32}$", telegram_username):
            raise ValueError("Pseudo Telegram invalide (lettres, chiffres, underscores, max 32 caractères)")
        
        mapping = UserManager.load_users()
        mapping[github_username.lower()] = telegram_username
        UserManager.save_users(mapping)

    @staticmethod
    def remove_user(github_username:str):
        mapping = UserManager.load_users()
        if github_username.lower() in mapping:
            del mapping[github_username.lower()]
            UserManager.save_users(mapping)
        else :
            raise Warning(f"Aucune correspondance trouvée pour {github_username}")
        
    @staticmethod
    def get_telegram_username(github_username:str)->str:
        mapping = UserManager.load_users()
        return mapping.get(github_username.lower(), github_username)
        