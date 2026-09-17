"""
Skill: fetch_pr_diff

Pulls a pull request's diff and changed-file list from the GitHub REST
API. Works without a token for public repos (rate-limited to 60 req/hr);
set GITHUB_TOKEN for private repos or higher limits.
"""

import os
from typing import Any, Dict, List

import requests

GITHUB_API = "https://api.github.com"


def _headers() -> Dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    """
    Returns:
      {
        "title": str,
        "body": str,
        "diff": str,               # unified diff, human/LLM readable
        "files": [                 # per-file patch + stats
          {"filename": ..., "status": ..., "additions": ..., "deletions": ..., "patch": ...}
        ]
      }
    """
    base_url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"

    meta_resp = requests.get(base_url, headers=_headers())
    meta_resp.raise_for_status()
    meta = meta_resp.json()

    diff_resp = requests.get(
        base_url, headers={**_headers(), "Accept": "application/vnd.github.v3.diff"}
    )
    diff_resp.raise_for_status()

    files_resp = requests.get(f"{base_url}/files", headers=_headers())
    files_resp.raise_for_status()
    files: List[Dict[str, Any]] = [
        {
            "filename": f["filename"],
            "status": f["status"],
            "additions": f["additions"],
            "deletions": f["deletions"],
            "patch": f.get("patch", ""),
        }
        for f in files_resp.json()
    ]

    return {
        "title": meta["title"],
        "body": meta.get("body") or "",
        "diff": diff_resp.text,
        "files": files,
    }
