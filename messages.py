# messages.py
EMOJI_PUSH = "🚀"
EMOJI_PR = "🔃"
EMOJI_PR_REVIEW = {
    "approved": "✅",
    "changes_requested": "🛑",
    "commented": "💬",
    "default": "🔔",
}
EMOJI_CREATE = "✨"
EMOJI_DELETE = "🗑️"
EMOJI_BRANCH = "🌿"
EMOJI_COMMIT = "📝"
EMOJI_AUTHOR = "👤"
EMOJI_LINK = "📎"
EMOJI_REVIEWERS = "👀"
EMOJI_PR_NUMBER = "📌"
EMOJI_TOOLS = "🔧" 


def format_push_message(repo_name, ref, commit_count, commit_message, sender_username, repo_url):
    return (
        f"{EMOJI_PUSH} **Nouveau Push sur** `{repo_name}`\n"
        f"{EMOJI_BRANCH} **Branche/Tag :** `{ref}`\n"
        f"{EMOJI_COMMIT} **Commits :** {commit_count}\n"
        f"{EMOJI_TOOLS} **Dernier commit :** {commit_message[:200]}...\n"
        f"{EMOJI_AUTHOR} **Auteur :** {sender_username}\n"
        f"{EMOJI_LINK} [Voir dépôt]({repo_url})"
    )

def format_pull_request_message(repo_name, pr_number, pr_title, head_branch, base_branch, sender_username, pr_reviewers_str, pr_url):
    return (
        f"{EMOJI_PR} **Nouvelle Pull Request sur** `{repo_name}`\n"
        f"{EMOJI_PR_NUMBER} **PR #{pr_number} :** {pr_title[:100]}...\n"
        f"{EMOJI_BRANCH} **Branche :** `{head_branch}` → `{base_branch}`\n"
        f"{EMOJI_AUTHOR} **Auteur :** {sender_username}\n"
        f"{EMOJI_REVIEWERS} **Reviewers assignés :** {pr_reviewers_str}\n"
        f"{EMOJI_LINK} [Voir PR]({pr_url})"
    )

def format_pull_request_review_message(emoji, reviewer, state_str, pr_author, pr_number, pr_title, body, pr_url):
    msg = (
        f"{emoji} {reviewer} {state_str} la PR de {pr_author} :\n"
        f"{EMOJI_PR_NUMBER} **PR #{pr_number} :** {pr_title[:100]}...\n"
    )
    if body:
        msg += f"**Commentaire :**\n{body[:200]}...\n"
    msg += f"{EMOJI_LINK} [Voir PR]({pr_url})"
    return msg

def format_create_event_message(action, repo_name, ref, sender_username, repo_url):
    return (
        f"{EMOJI_CREATE} **{action} :** `{repo_name}`\n"
        f"{EMOJI_BRANCH} **Nom :** `{ref}`\n"
        f"{EMOJI_AUTHOR} **Auteur :** {sender_username}\n"
        f"{EMOJI_LINK} [Voir dépôt]({repo_url})"
    )

def format_delete_event_message(action, repo_name, ref, sender_username, repo_url):
    return (
        f"{EMOJI_DELETE} **{action} :** `{repo_name}`\n"
        f"{EMOJI_BRANCH} **Nom :** `{ref}`\n"
        f"{EMOJI_AUTHOR} **Auteur :** {sender_username}\n"
        f"{EMOJI_LINK} [Voir dépôt]({repo_url})"
    )

# Fonction pour remplacer les caractères spéciaux Markdown, proposée par chatGPT
def escape_markdown(text: str) -> str:
    return text.replace('*', '').replace('_', '').replace('[', '').replace(']', '')