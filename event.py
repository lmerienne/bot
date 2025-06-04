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
        is_new_branch = self.data.get("created", False) and self.data.get("before", "").startswith("000")
        is_deleted_branch = self.data.get("deleted", False) and self.data.get("after", "").startswith("000")

        if is_new_branch:
            return (
                f"✨ **Nouvelle branche créée :** `{common_info['repo_name']}`\n"
                f"🌿 **Branche :** `{ref}`\n"
                f"👤 **Auteur :** {common_info['sender_username']}\n"
                f"📎 [Voir dépôt]({common_info['repo_url']})"
            )

        if is_deleted_branch:
            return (
                f"🗑️ **Branche supprimée :** `{common_info['repo_name']}`\n"
                f"🌿 **Branche :** `{ref}`\n"
                f"👤 **Auteur :** {common_info['sender_username']}\n"
                f"📎 [Voir dépôt]({common_info['repo_url']})"
            )

        return (
            f"🚀 **Nouveau Push sur** `{common_info['repo_name']}`\n"
            f"🌿 **Branche/Tag :** `{ref}`\n"
            f"📝 **Commits :** `{commit_count}`\n"
            f"🔧 **Dernier commit :** `{commit_message[:500]}`...\n"
            f"👤 **Auteur :** `{common_info['sender_username']}`\n"
            f"📎 [Voir dépôt]({common_info['repo_url']}) "
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
        head_branch = pr.get("head", {}).get("ref", "inconnue")
        base_branch = pr.get("base", {}).get("ref", "inconnue")

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
            f"🔃 **Nouvelle Pull Request sur** `{common_info['repo_name']}`\n"
            f"📌 **PR #{pr_number} :** `{pr_title[:100]}`...\n"
            f"🌿 **Branche/Tag :** `{head_branch}` → `{base_branch}`\n"
            f"👤 **Auteur :** `{common_info['sender_username']}`\n"
            f"👀 `{pr_reviewers_str}`\n"
            f"📎 [Voir PR]({pr_url}) "
        )
    
class PullRequestReviewEvent(GitHubEvent):
    def format_message(self)->str:
        common_info = self.get_info()
        review = self.data.get("review", {})
        pr = self.data.get("pull_request", {})
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
        state_map = {
            "approved":          ("✅", "a approuvé"),
            "changes_requested": ("🛑", "a demandé des changements sur"),
            "commented":         ("💬", "a commenté"),
        }
        emoji, state_str = state_map.get(state, ("🔔", "a fait une review sur"))

        body = review.get("body", "")
        msg = (
            f"{emoji} `{reviewer}` `{state_str}` la PR de `{pr_author}` :\n"
            f"📌 **PR #`{pr_number}` :** `{pr_title[:500]}`...\n"
        )

        if body:
            msg += f"**Commentaire :**\n`{body[:500]}`...\n"
        
        msg += f"📎 [Voir PR]({pr_url})"
        return msg
    
class CreateBranchEvent(GitHubEvent):
    def format_message(self)->str:
        common_info = self.get_info()
        ref_type = self.data.get("ref_type")
        ref = self.data.get("ref")

        if ref_type == "branch":
            action = "Nouvelle branche créée"
        else :
            action = "Nouveau Tag créé"

        return (
            f"✨ **`{action}` :** `{common_info['repo_name']}`\n"
            f"🌿 **Branch/Tag :** `{ref}`\n"
            f"👤 **Auteur :** `{common_info['sender_username']}`\n"
            f"📎 [Voir dépôt]({common_info['repo_url']})"
        )
    
class DeleteBranchEvent(GitHubEvent):
    def format_message(self):
        common_info = self.get_info()
        ref_type = self.data.get("ref_type")
        ref = self.data.get("ref")

        if ref_type == "branch":
            action = "Branche supprimée"
        else :
            action = "Tag supprimé"
        
        return (
            f"🗑️ **`{action}` :** `{common_info['repo_name']}`\n"
            f"🌿 **Branch/Tag :** `{ref}`\n"
            f"👤 **Auteur :** `{common_info['sender_username']}`\n"
            f"📎 [Voir dépôt]({common_info['repo_url']})"
        )

EVENT_CLASSES = {
    "push": PushEvent,
    "pull_request": PullRequestEvent,
    "pull_request_review": PullRequestReviewEvent,
    "create_branch_event" : CreateBranchEvent,
    "delete_branch_event" : DeleteBranchEvent
}