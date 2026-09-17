"""
Skill: save_excluded_files

Records which files were skipped from review and why, for audit purposes.
"""

from typing import Any, Dict, List

from src.skills.filter_reviewable_files import get_excluded_patterns, is_reviewable
from src.skills.save_review_to_db import get_connection


def _matched_pattern(filename: str, patterns: List[str]) -> str:
    import fnmatch
    for pattern in patterns:
        if fnmatch.fnmatch(filename, pattern):
            return pattern
    return ""


def save_excluded_files(
    owner: str, repo: str, pr_number: int, excluded_files: List[Dict[str, Any]]
) -> None:
    if not excluded_files:
        return
    patterns = get_excluded_patterns()
    rows = [
        (owner, repo, pr_number, f["filename"], _matched_pattern(f["filename"], patterns))
        for f in excluded_files
    ]
    query = """
        INSERT INTO pr_review_excl (owner, repo, pr_number, filename, matched_pattern)
        VALUES (%s, %s, %s, %s, %s);
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(query, rows)
        conn.commit()