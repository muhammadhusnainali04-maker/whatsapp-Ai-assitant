"""
Central settings, loaded once from .env.
Every other module imports `settings` from here instead of reading os.environ directly.
"""
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    # backend / auth
    webhook_api_key: str = os.getenv("WEBHOOK_API_KEY", "")
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))

    # database
    database_path: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "database" / "app.db"))

    # groq — same parameter shape as the client's Section 5.1 LLM configuration table,
    # swapped from Gemini to Groq per Husnain's decision
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    groq_temperature: float = float(os.getenv("GROQ_TEMPERATURE", "0.4"))
    groq_top_p: float = float(os.getenv("GROQ_TOP_P", "0.9"))
    groq_max_output_tokens: int = int(os.getenv("GROQ_MAX_OUTPUT_TOKENS", "512"))
    groq_timeout_seconds: int = int(os.getenv("GROQ_TIMEOUT_SECONDS", "15"))

    # app1transcribe
    app1transcribe_api_key: str = os.getenv("APP1TRANSCRIBE_API_KEY", "")
    app1transcribe_url: str = os.getenv("APP1TRANSCRIBE_URL", "")

    # whatsapp cloud api (test number for MVP — see README)
    whatsapp_access_token: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    whatsapp_verify_token: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")

    # context/memory strategy — Section 5.3
    history_message_count: int = 10
    history_token_budget: int = 3000


settings = Settings()

if not settings.webhook_api_key or settings.webhook_api_key == "change-me-to-a-long-random-string":
    print("[config] WARNING: WEBHOOK_API_KEY is not set to a real secret yet.")
