"""
Skill: post_review_comment

Posts the synthesized review as an issue comment on the PR. Kept separate
from the review pipeline and never called automatically — main.py only
invokes this if the user passes --post, since writing to a real repo
should always be an explicit, opt-in action.
"""

import os
from typing import Any, Dict

import requests

GITHUB_API = "https://api.github.com"


def post_review_comment(owner: str, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is required to post comments (read-only fetch works without it)."
        )
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    resp = requests.post(url, headers=headers, json={"body": body})
    resp.raise_for_status()
    return resp.json()
