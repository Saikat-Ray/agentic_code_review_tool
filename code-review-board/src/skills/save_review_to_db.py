"""
Skill: save_review_to_db

Persists a review for moderation: one row in pr_reviews per review run,
one row per agent's comment in pr_review_comments. Adding a new agent
later needs no schema change — just another row with its agent_name.
"""

import os
from typing import Dict

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set.")
    return psycopg2.connect(database_url)


def save_review_to_db(
    owner: str,
    repo: str,
    pr_number: int,
    agent_comments: Dict[str, str],
    final_review: str,
) -> int:
    """
    agent_comments: {"correctness_agent": "...", "security_agent": "...", ...}
    Returns the new pr_reviews.id.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pr_reviews (owner, repo, pr_number, final_review)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (owner, repo, pr_number, final_review),
            )
            review_id = cur.fetchone()[0]

            cur.executemany(
                """
                INSERT INTO pr_review_comments (review_id, agent_name, comment)
                VALUES (%s, %s, %s);
                """,
                [(review_id, agent_name, comment) for agent_name, comment in agent_comments.items()],
            )
        conn.commit()
    return review_id


def get_pending_reviews():
    query = "SELECT * FROM pr_reviews WHERE status = 'pending_moderation' ORDER BY created_at;"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return cur.fetchall()


def get_comments_for_review(review_id: int):
    query = "SELECT * FROM pr_review_comments WHERE review_id = %s ORDER BY agent_name;"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (review_id,))
            return cur.fetchall()


def update_review_status(review_id: int, status: str, moderator_notes: str = "") -> None:
    query = """
        UPDATE pr_reviews
        SET status = %s, moderator_notes = %s, moderated_at = now()
        WHERE id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (status, moderator_notes, review_id))
        conn.commit()