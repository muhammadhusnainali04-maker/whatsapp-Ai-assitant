"""
Thin App1Transcribe wrapper. Like groq_service, the main pipeline calls
App1Transcribe directly from n8n — this exists only if you ever need to
transcribe from the Python side (e.g. testing, or a manual re-transcribe button).

NOTE: verify this against App1Transcribe's actual API docs before relying on it —
the request/response shape below is taken from the client's own spec
(POST audio file -> {"text": "..."}), but field names, auth header, and content-type
may differ in the real API and should be confirmed.
"""
import requests

from config import settings


def transcribe_audio(file_path: str) -> str:
    with open(file_path, "rb") as f:
        response = requests.post(
            settings.app1transcribe_url,
            headers={"Authorization": f"Bearer {settings.app1transcribe_api_key}"},
            files={"audio": f},
            timeout=60,
        )
    response.raise_for_status()
    return response.json()["text"]
