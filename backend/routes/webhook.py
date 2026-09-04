from fastapi import APIRouter, Depends

from backend.middleware import verify_api_key
from database import database as db
from models.message import IncomingWebhookPayload, WebhookResponse

router = APIRouter()


@router.post("/webhook/incoming", response_model=WebhookResponse, dependencies=[Depends(verify_api_key)])
def receive_incoming(payload: IncomingWebhookPayload):
    conversation_id = db.get_or_create_conversation(
        sender_id=payload.sender_id,
        sender_name=payload.sender_name,
        channel=payload.channel,
    )

    message_id = db.insert_incoming_message(
        conversation_id=conversation_id,
        message_type=payload.message_type,
        original_text=payload.original_text,
        transcript=payload.transcript,
        platform_message_id=payload.platform_message_id,
    )

    if message_id is None:
        # Duplicate delivery of a message we've already seen — discard silently,
        # this is what keeps a resent WhatsApp webhook delivery from creating a second reply.
        db.log("info", "webhook", f"Duplicate platform_message_id ignored: {payload.platform_message_id}")
        return WebhookResponse(status="duplicate_ignored", detail="Message already recorded")

    reply_id = db.insert_ai_reply(
        message_id=message_id,
        generated_reply=payload.generated_reply,
        n8n_resume_url=payload.n8n_resume_url,
        n8n_execution_id=payload.n8n_execution_id,
        n8n_workflow_id=payload.n8n_workflow_id,
        input_tokens=payload.input_tokens,
        output_tokens=payload.output_tokens,
        api_cost=payload.api_cost,
    )

    db.log("info", "webhook", f"Stored message {message_id}, reply {reply_id} pending review")
    return WebhookResponse(status="pending_review", message_id=message_id, reply_id=reply_id)
