# event.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from user import UserManager
from messages import (
    format_push_message, format_pull_request_message, format_pull_request_review_message,
    format_create_event_message, format_delete_event_message,
    EMOJI_PR_REVIEW, escape_markdown
)

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
            "repo_name": escape_markdown(self.repo.get("full_name", "Unknown")),
            "repo_url": self.repo.get("html_url", " "),
            "sender_username": sender_username,
            "sender_url": self.sender.get("html_url", " ")
        }
    
class PushEvent(GitHubEvent):
    def format_message(self) -> str:
        common_info = self.get_info()
        ref = escape_markdown(self.data.get("ref", "").replace("refs/heads/", "").replace("refs/tags/", ""))
        commits = self.data.get("commits", [])
        commit_count = len(commits)
        head_commit = self.data.get("head_commit", {})
        commit_message = escape_markdown(head_commit.get("message", "Aucun message") if head_commit else "Aucun message")
        is_new_branch = self.data.get("created", False) and self.data.get("before", "").startswith("000")
        is_deleted_branch = self.data.get("deleted", False) and self.data.get("after", "").startswith("000")

        if is_new_branch:
            return format_create_event_message(
                action="Nouvelle branche créée",
                repo_name=common_info['repo_name'],
                ref=ref,
                sender_username=common_info['sender_username'],
                repo_url=common_info['repo_url']
            )

        if is_deleted_branch:
            return format_delete_event_message(
                action="Branche supprimée",
                repo_name=common_info['repo_name'],
                ref=ref,
                sender_username=common_info['sender_username'],
                repo_url=common_info['repo_url']
            )

        return format_push_message(
            repo_name=common_info['repo_name'],
            ref=ref,
            commit_count=commit_count,
            commit_message=commit_message,
            sender_username=common_info['sender_username'],
            repo_url=common_info['repo_url']
        )

class PullRequestEvent(GitHubEvent):
    def format_message(self) -> str:
        common_info = self.get_info()
        pr = self.data.get("pull_request", {})
        pr_number = pr.get("number", "N/A")
        pr_title = escape_markdown(pr.get("title", "Aucun titre"))
        pr_url = pr.get("html_url", " ")
        pr_reviewers = pr.get("requested_reviewers", [])

        github_reviewers = [user.get("login") for user in pr_reviewers if user.get("login")]
        telegram_reviewers = []
        head_branch = escape_markdown(pr.get("head", {}).get("ref", "inconnue"))
        base_branch = escape_markdown(pr.get("base", {}).get("ref", "inconnue"))

        for github_user in github_reviewers:
            tg_username = UserManager.get_telegram_username(github_user)
            if tg_username:
                telegram_reviewers.append(f"@{tg_username}")
            else:
                telegram_reviewers.append(github_user)

        pr_reviewers_str = ""
        if telegram_reviewers:
            pr_reviewers_str = ", ".join(telegram_reviewers)

        return format_pull_request_message(
            repo_name=common_info['repo_name'],
            pr_number=pr_number,
            pr_title=pr_title,
            head_branch=head_branch,
            base_branch=base_branch,
            sender_username=common_info['sender_username'],
            pr_reviewers_str=pr_reviewers_str,
            pr_url=pr_url
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
        pr_title = escape_markdown(pr.get("title", "Aucun titre"))
        pr_url = pr.get("html_url", " ")
        pr_author_github = pr.get("user", {}).get("login", "Unknown")
        pr_author_telegram = UserManager.get_telegram_username(pr_author_github)
        pr_author = f"@{pr_author_telegram}" if pr_author_telegram else pr_author_github

        state = review.get("state", "commented").lower()
        emoji, state_str = EMOJI_PR_REVIEW.get(state, (EMOJI_PR_REVIEW["default"], "**a fait une review sur**"))

        body = escape_markdown(review.get("body", ""))

        return format_pull_request_review_message(
            emoji=emoji,
            reviewer=reviewer,
            state_str=state_str,
            pr_author=pr_author,
            pr_number=pr_number,
            pr_title=pr_title,
            body=body,
            pr_url=pr_url
        )
    
class CreateEvent(GitHubEvent):
    def format_message(self)->str:
        common_info = self.get_info()
        ref_type = self.data.get("ref_type")
        ref = escape_markdown(self.data.get("ref", ""))

        action = "Créé"
        if ref_type == "branch":
            action_type = "branche"
        elif ref_type == "tag":
            action_type = "tag"
        else:
            action_type = f"objet ({ref_type})"

        return format_create_event_message(
            action=f"Nouvel {action_type} {action}",
            repo_name=common_info['repo_name'],
            ref=ref,
            sender_username=common_info['sender_username'],
            repo_url=common_info['repo_url']
        )
    
class DeleteEvent(GitHubEvent):
    def format_message(self):
        common_info = self.get_info()
        ref_type = self.data.get("ref_type")
        ref = escape_markdown(self.data.get("ref", ""))

        action = "Supprimé"
        if ref_type == "branch":
            action_type = "branche"
        elif ref_type == "tag":
            action_type = "tag"
        else:
            action_type = f"objet ({ref_type})"

        return format_delete_event_message(
            action=f"{action_type.capitalize()} {action}",
            repo_name=common_info['repo_name'],
            ref=ref,
            sender_username=common_info['sender_username'],
            repo_url=common_info['repo_url']
        )

EVENT_CLASSES = {
    "push": PushEvent,
    "pull_request": PullRequestEvent,
    "pull_request_review": PullRequestReviewEvent,
    "create_branch_event" : CreateEvent,
    "delete_branch_event" : DeleteEvent,
}