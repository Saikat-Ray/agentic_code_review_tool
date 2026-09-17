"""
Skill: filter_reviewable_files

Drops files that shouldn't go through LLM review — config, lockfiles,
docs, plain text, images — before the diff reaches any reviewer agent.
Excluded patterns come from EXCLUDED_FILE_PATTERNS in .env.
"""

import fnmatch
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

DEFAULT_EXCLUDED_PATTERNS = [
    "*.txt", "*.md", "*.rst",
    "*.json", "*.yml", "*.yaml", "*.toml", "*.ini", "*.cfg",
    "*.lock", "package-lock.json", "poetry.lock", "Pipfile.lock",
    "*.env", "*.env.*", ".gitignore", ".gitattributes",
    "*.svg", "*.png", "*.jpg", "*.jpeg",
]


def get_excluded_patterns() -> List[str]:
    raw = os.environ.get("EXCLUDED_FILE_PATTERNS")
    if not raw:
        return DEFAULT_EXCLUDED_PATTERNS
    return [p.strip() for p in raw.split(",") if p.strip()]


def is_reviewable(filename: str, excluded_patterns: List[str]) -> bool:
    return not any(fnmatch.fnmatch(filename, pattern) for pattern in excluded_patterns)


def filter_reviewable_files(files: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Returns {"included": [...], "excluded": [...]} — main.py needs both,
    the excluded list to persist to pr_review_excl."""
    patterns = get_excluded_patterns()
    included, excluded = [], []
    for f in files:
        (included if is_reviewable(f["filename"], patterns) else excluded).append(f)
    return {"included": included, "excluded": excluded}


def rebuild_diff_from_files(files: List[Dict[str, Any]]) -> str:
    parts = [
        f"diff --git a/{f['filename']} b/{f['filename']}\n{f.get('patch', '')}"
        for f in files
    ]
    return "\n".join(parts)