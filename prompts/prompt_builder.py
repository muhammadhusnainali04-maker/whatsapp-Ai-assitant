"""
Builds the final prompt sent to the LLM (Groq):
    system prompt -> business rules -> conversation history -> current message

Truncation strategy (Section 5.3): keep the most recent N messages, and if the
rough token budget is exceeded, drop the oldest messages first while always
keeping the most recent 3 regardless of budget.
"""
from pathlib import Path

from config import settings

PROMPTS_DIR = Path(__file__).parent

SYSTEM_PROMPT = (PROMPTS_DIR / "system_prompt.txt").read_text()
BUSINESS_RULES = (PROMPTS_DIR / "business_rules.txt").read_text()


def _approx_tokens(text: str) -> int:
    # Rough estimate (~4 chars/token). Good enough for a soft budget check;
    # replace with a real tokenizer if precise counts matter later.
    return max(1, len(text) // 4)


def _format_history(messages: list) -> list[str]:
    """messages: sqlite3.Row objects from database.get_recent_messages, oldest first."""
    lines = []
    for m in messages:
        text = m["transcript"] or m["original_text"] or ""
        role = "Customer" if m["direction"] == "incoming" else "Assistant"
        lines.append(f"{role}: {text}")
    return lines


def build_prompt(history_rows: list, current_message: str) -> str:
    history_lines = _format_history(history_rows[-settings.history_message_count:])

    # Keep the most recent 3 no matter what; drop older ones if over budget
    budget = settings.history_token_budget
    kept = list(history_lines)
    while len(kept) > 3 and _approx_tokens("\n".join(kept)) > budget:
        kept.pop(0)

    history_block = "\n".join(kept) if kept else "(no prior messages)"

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Business rules:\n{BUSINESS_RULES}\n\n"
        f"Conversation history:\n{history_block}\n\n"
        f"Current message:\nCustomer: {current_message}\n\n"
        f"Write the assistant's reply only — no labels, no extra commentary."
    )
