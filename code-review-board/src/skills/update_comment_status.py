"""
Skill: update_comment_status

Writes the moderator's per-comment verdicts back to pr_review_comments.
"""

from typing import Any, Dict, List

from src.skills.save_review_to_db import get_connection


def update_comment_status(verdicts: List[Dict[str, Any]]) -> None:
    query = """
        UPDATE pr_review_comments
        SET status = %s, moderator_notes = %s
        WHERE id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                query, [(v["status"], v.get("notes", ""), v["id"]) for v in verdicts]
            )
        conn.commit()