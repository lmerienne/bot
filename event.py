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
            f"Dernier commit : {commit_message[:500]}...\n"
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
        pr_reviewers = pr.get("requested_reviewers", [])

        github_reviewers = [user.get("login") for user in pr_reviewers if user.get("login")]
        telegram_reviewers = []

        for github_user in github_reviewers:
            tg_username = UserManager.get_telegram_username(github_user)
            if tg_username:
                telegram_reviewers.append(f"@{tg_username}")
            else:
                telegram_reviewers.append(github_user)

        pr_reviewers_str = ""
        if telegram_reviewers:
            pr_reviewers_str = "Reviewers : " + ", ".join(telegram_reviewers)

        return (
            f"Nouvelle Pull Request sur {common_info['repo_name']}\n"
            f"PR #{pr_number} : {pr_title[:100]}...\n"
            f"Par : {common_info['sender_username']}\n"
            f"{pr_reviewers_str}\n"
            f"[Voir PR]({pr_url}) "
        )
    
class PullRequestReviewEvent(GitHubEvent):
    def format_message(self)->str:
        common_info = self.get_info()
        review = self.data.get("review", {})
        pr = self.data.get("pulle_request", {})
        reviewer_github = review.get("user", {}).get("login", "Unknown")
        reviewer_telegram = UserManager.get_telegram_username(reviewer_github)
        reviewer = f"@{reviewer_telegram}" if reviewer_telegram else reviewer_github

        pr_number = pr.get("number", "N/A")
        pr_title = pr.get("title", "Aucun titre")
        pr_url = pr.get("html_url", " ")
        pr_author_github = pr.get("user", {}).get("login", "Unknown")
        pr_author_telegram = UserManager.get_telegram_username(pr_author_github)
        pr_author = f"@{pr_author_telegram}" if pr_author_telegram else pr_author_github

        state = review.get("state", "commented").lower()
        state_str = {
            "approved": "a approuvé",
            "changes_requested": "a demandé des changements sur",
            "commented": "a commenté"
        }.get(state, f"a fait une review sur")

        body = review.get("body", "")

        msg = (
            f"{reviewer} {state_str} la PR de {pr_author} :\n"
            f"PR #{pr_number} : {pr_title[:500]}...\n"
        )

        if body:
            msg += f"Commentaire :\n{body[:500]}...\n"
        
        msg += f"[Voir PR]({pr_url})"

        return msg

EVENT_CLASSES = {
    "push": PushEvent,
    "pull_request": PullRequestEvent,
    "pull_request_review": PullRequestReviewEvent,
}