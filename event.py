from abc import ABC, abstractmethod
from typing import Dict, Any
from user import UserManager

class GitHubEvent(ABC):
    def __init__(self, data: Dict[str, any]):
        self.data = data
        self.repo = data.get("repository", {})
        self.sender = data.get("sender", {})
        self.action = data.get("action", None)
    
    @abstractmethod
    def format_message(self) -> str:
        pass
    
    def get_info(self) -> Dict[str, Any]:
        github_username = self.sender.get("login", "Unknown")
        telegram_username = UserManager.get_telegram_username(github_username)
        sender_username = f"@{telegram_username}" if telegram_username else github_username

        return {
            "repo_name": self.repo.get("full_name", "Unknown"),
            "repo_url": self.repo.get("html_url", " "),
            "sender_username": sender_username,
            "sender_url": self.sender.get("html_url", " ")
        }
    
class PushEvent(GitHubEvent):
    def format_message(self) -> str:
        common_info = self.get_info()
        ref = self.data.get("ref", "").replace("refs/heads/", "").replace("refs/tags/", "")
        commits = self.data.get("commits", [])
        commit_count = len(commits)
        head_commit = self.data.get("head_commit", {})
        commit_message = head_commit.get("message", "Aucun message") if head_commit else "Aucun message"

        return (
            f"Nouveau push sur {common_info['repo_name']}\n"
            f"Branche/Tag : {ref}\n"
            f"Commits : {commit_count}\n"
            f"Dernier commit : {commit_message[:100]}...\n"
            f"Par : {common_info['sender_username']}\n"
            f"[Voir dépôt]({common_info['repo_url']}) "
        )

class PullRequestEvent(GitHubEvent):
    def format_message(self) -> str:
        common_info = self.get_info()
        pr = self.data.get("pull_request", {})
        pr_number = pr.get("number", "N/A")
        pr_title = pr.get("title", "Aucun titre")
        pr_url = pr.get("html_url", " ")

        return (
            f"Nouvelle Pull Request sur {common_info['repo_name']}\n"
            f"PR #{pr_number} : {pr_title[:100]}...\n"
            f"Par : {common_info['sender_username']}\n"
            f"[Voir PR]({pr_url}) "
        )

EVENT_CLASSES = {
    "push": PushEvent,
    "pull_request": PullRequestEvent,
}