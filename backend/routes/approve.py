import time

import requests
from fastapi import APIRouter, Depends, HTTPException

from backend.middleware import verify_api_key
from database import database as db
from models.message import ApprovePayload, WebhookResponse

router = APIRouter()

RESUME_TIMEOUT_SECONDS = 15
MAX_ATTEMPTS = 3


@router.post("/approve/{reply_id}", response_model=WebhookResponse, dependencies=[Depends(verify_api_key)])
def approve(reply_id: int, payload: ApprovePayload):
    reply = db.get_reply_by_id(reply_id)
    if reply is None:
        raise HTTPException(status_code=404, detail="Reply not found")

    db.approve_reply(reply_id, edited_reply=payload.edited_reply, edited_by=payload.edited_by)

    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                reply["n8n_resume_url"],
                json={"approved_reply": payload.edited_reply},
                timeout=RESUME_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            db.log("info", "approve", f"Resumed n8n for reply {reply_id} on attempt {attempt}")
            return WebhookResponse(status="approved", reply_id=reply_id)
        except requests.RequestException as exc:
            last_error = exc
            db.log("error", "approve", f"Resume attempt {attempt} failed for reply {reply_id}: {exc}")
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 ** attempt)  # exponential backoff: 2s, 4s

    # All attempts failed — mark it so the review UI shows a failed state
    # instead of leaving the operator thinking it sent.
    db.mark_failed(reply_id)
    raise HTTPException(
        status_code=502,
        detail=(
            f"Could not resume n8n workflow after {MAX_ATTEMPTS} attempts "
            f"(resume_url may have expired — execution_id is stored as a fallback "
            f"for manual recovery: {reply['n8n_execution_id']}). Last error: {last_error}"
        ),
    )


@router.post("/reject/{reply_id}", response_model=WebhookResponse, dependencies=[Depends(verify_api_key)])
def reject(reply_id: int):
    if db.get_reply_by_id(reply_id) is None:
        raise HTTPException(status_code=404, detail="Reply not found")
    db.reject_reply(reply_id)
    return WebhookResponse(status="rejected", reply_id=reply_id)
