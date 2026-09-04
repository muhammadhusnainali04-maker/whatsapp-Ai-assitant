"""
Thin SQLite access layer. Deliberately plain sqlite3 (not an ORM) to keep the
3-day build fast. When M9 swaps to PostgreSQL, only this file and schema.sql
need to change — nothing in backend/ or frontend/ should import sqlite3 directly.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import settings

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db() -> None:
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text())


@contextmanager
def get_connection():
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ---------- conversations ----------

def get_or_create_conversation(sender_id: str, sender_name: str | None, channel: str = "whatsapp") -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM conversations WHERE sender_id = ? AND channel = ?",
            (sender_id, channel),
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO conversations (sender_id, sender_name, channel) VALUES (?, ?, ?)",
            (sender_id, sender_name, channel),
        )
        return cur.lastrowid


# ---------- messages (idempotent on platform_message_id) ----------

def insert_incoming_message(
    conversation_id: int,
    message_type: str,
    original_text: str | None,
    transcript: str | None,
    platform_message_id: str,
) -> int | None:
    """Returns the new message id, or None if this platform_message_id was already stored
    (duplicate webhook delivery — the UNIQUE constraint on the column is what actually
    enforces this; this function just makes the "discard duplicates" behavior explicit)."""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM messages WHERE platform_message_id = ?", (platform_message_id,)
        ).fetchone()
        if existing:
            return None
        cur = conn.execute(
            """INSERT INTO messages
               (conversation_id, direction, message_type, original_text, transcript, platform_message_id)
               VALUES (?, 'incoming', ?, ?, ?, ?)""",
            (conversation_id, message_type, original_text, transcript, platform_message_id),
        )
        return cur.lastrowid


def get_recent_messages(conversation_id: int, limit: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """SELECT * FROM messages WHERE conversation_id = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (conversation_id, limit),
        ).fetchall()[::-1]  # oldest first


# ---------- ai_replies ----------

def insert_ai_reply(
    message_id: int,
    generated_reply: str,
    n8n_resume_url: str,
    n8n_execution_id: str,
    n8n_workflow_id: str,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    api_cost: float | None = None,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO ai_replies
               (message_id, generated_reply, status, n8n_resume_url, n8n_execution_id,
                n8n_workflow_id, input_tokens, output_tokens, api_cost)
               VALUES (?, ?, 'pending_review', ?, ?, ?, ?, ?, ?)""",
            (message_id, generated_reply, n8n_resume_url, n8n_execution_id,
             n8n_workflow_id, input_tokens, output_tokens, api_cost),
        )
        return cur.lastrowid


def get_pending_replies() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """SELECT ai_replies.*, messages.original_text, messages.transcript,
                      messages.message_type, conversations.sender_name, conversations.sender_id
               FROM ai_replies
               JOIN messages ON messages.id = ai_replies.message_id
               JOIN conversations ON conversations.id = messages.conversation_id
               WHERE ai_replies.status = 'pending_review'
               ORDER BY ai_replies.created_at ASC"""
        ).fetchall()


def get_reply_by_id(reply_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM ai_replies WHERE id = ?", (reply_id,)).fetchone()


def approve_reply(reply_id: int, edited_reply: str, edited_by: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """UPDATE ai_replies
               SET status = 'approved', edited_reply = ?, edited_by = ?, edited_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (edited_reply, edited_by, reply_id),
        )


def reject_reply(reply_id: int) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE ai_replies SET status = 'rejected' WHERE id = ?", (reply_id,))


def mark_sent(reply_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE ai_replies SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE id = ?",
            (reply_id,),
        )


def mark_failed(reply_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE ai_replies SET status = 'failed', retry_count = retry_count + 1 WHERE id = ?",
            (reply_id,),
        )


# ---------- logs ----------

def log(level: str, source: str, message: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO logs (level, source, message) VALUES (?, ?, ?)",
            (level, source, message),
        )
