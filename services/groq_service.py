"""
Thin Groq wrapper. The main pipeline calls Groq directly from n8n (see
n8n/workflow_export.json) — this module exists so the Streamlit "Regenerate"
button can call Groq again without waking up a paused n8n execution.
"""
from groq import Groq

from config import settings
from prompts.prompt_builder import build_prompt

client = Groq(api_key=settings.groq_api_key)

# Groq pricing varies by model — update these to match settings.groq_model.
# Figures below are illustrative; confirm against Groq's current pricing page.
_INPUT_COST_PER_1K = 0.00005
_OUTPUT_COST_PER_1K = 0.00008


def generate_reply(history_rows: list, current_message: str) -> dict:
    """Returns {"reply": str, "input_tokens": int, "output_tokens": int, "api_cost": float}."""
    prompt = build_prompt(history_rows, current_message)

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=settings.groq_temperature,
        top_p=settings.groq_top_p,
        max_tokens=settings.groq_max_output_tokens,
        timeout=settings.groq_timeout_seconds,
    )

    usage = response.usage
    input_tokens = getattr(usage, "prompt_tokens", 0) or 0
    output_tokens = getattr(usage, "completion_tokens", 0) or 0
    api_cost = (input_tokens / 1000) * _INPUT_COST_PER_1K + (output_tokens / 1000) * _OUTPUT_COST_PER_1K

    return {
        "reply": response.choices[0].message.content.strip(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "api_cost": round(api_cost, 6),
    }
