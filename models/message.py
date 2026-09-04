from pydantic import BaseModel


class IncomingWebhookPayload(BaseModel):
    """What n8n POSTs to /webhook/incoming after it has already detected the
    message type, transcribed voice if needed, and generated the Groq reply."""
    sender_id: str
    sender_name: str | None = None
    channel: str = "whatsapp"
    platform_message_id: str
    message_type: str  # "text" | "voice"
    original_text: str | None = None
    transcript: str | None = None
    generated_reply: str
    n8n_resume_url: str
    n8n_execution_id: str
    n8n_workflow_id: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    api_cost: float | None = None


class ApprovePayload(BaseModel):
    edited_reply: str
    edited_by: str = "operator"


class WebhookResponse(BaseModel):
    status: str
    message_id: int | None = None
    reply_id: int | None = None
    detail: str | None = None
