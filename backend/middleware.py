from fastapi import Header, HTTPException

from config import settings


def verify_api_key(x_api_key: str = Header(...)) -> None:
    if x_api_key != settings.webhook_api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")
