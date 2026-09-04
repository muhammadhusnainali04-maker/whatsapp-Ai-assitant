# WhatsApp AI Assistant — MVP scaffold (Day 1)

Adapted from the client's "Reviewed & Updated Technical Implementation Plan":
same architecture (n8n orchestration, FastAPI + SQLite for storage/review), but
swapped Telegram -> WhatsApp Cloud API (test number) and Gemini -> Groq per
Husnain's decision.

**Why the WhatsApp test number and not full business verification:** Meta's
business verification/app review can take days and is outside your control —
not something to depend on inside a 3-day window. The free test number (any
developer account gets one instantly when you create a WhatsApp app in Meta
for Developers) sends/receives real WhatsApp messages immediately, capped at
5 registered recipient numbers until you verify a real business later. Same
"fast now, upgrade later" logic the client's own plan used for Telegram.

## What's here

```
config.py                  central settings (loaded from .env)
database/schema.sql        tables: conversations, messages, ai_replies, prompt_versions, settings, logs
database/database.py       all SQLite queries — swap to Postgres later by editing only this file
models/message.py          request/response schemas for the API
prompts/                   system prompt, business rules, and the prompt assembly logic
services/groq_service.py   used by the Streamlit "Regenerate" button (main flow calls Groq from n8n)
services/transcribe_service.py  same idea, for App1Transcribe
backend/api.py             FastAPI app — /webhook/incoming, /approve/{id}, /reject/{id}, /health
frontend/chat_review.py    Streamlit review screen — this is what the operator uses
n8n/workflow_export.json   importable starting point for the n8n workflow
```

## What's NOT here yet (by design)

Dashboard/history pages, prompt versioning UI, full audit trail polish, cost
roll-ups, retry/backoff beyond the approve endpoint, automated tests — these
are later-milestone/Phase-2 items. The goal of this scaffold is a working
end-to-end loop.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real API keys and a random WEBHOOK_API_KEY
```

### Getting WhatsApp test number credentials

1. Go to developers.facebook.com -> create an app -> add the "WhatsApp" product.
2. Meta auto-provisions a free test number under WhatsApp > API Setup. From
   that page, copy the **temporary access token** (valid ~24h — swap for a
   permanent token via a System User once things are stable) and the
   **Phone number ID**.
3. Under "To" recipients, add up to 5 real phone numbers (yours, testers') —
   messages only work with numbers explicitly added here until business
   verification is done.
4. Set `WHATSAPP_VERIFY_TOKEN` in `.env` to any string you choose — you'll
   enter this same string in Meta's webhook config in step 4 of n8n setup below.

### Getting a Groq API key

console.groq.com -> API Keys -> create one. Free tier is generous and fast
enough for MVP testing.

## Run

```bash
# Terminal 1 — backend
uvicorn backend.api:app --reload --port 8000

# Terminal 2 — review UI
streamlit run frontend/chat_review.py

# Terminal 3 — tunnel so Meta can reach your local n8n webhook
ngrok http 5678   # (assuming n8n runs on its default port)
```

## n8n setup

1. Import `n8n/workflow_export.json` into your n8n instance.
2. Create a WhatsApp Trigger credential in n8n using the access token and
   phone number ID from above.
3. Save the workflow once so the WhatsApp Trigger and Wait nodes generate
   real webhook URLs.
4. In Meta's app dashboard, set the webhook callback URL to your ngrok URL +
   the WhatsApp Trigger's webhook path, and the verify token to match
   `WHATSAPP_VERIFY_TOKEN`. Subscribe to the `messages` field.
5. Set environment variables in n8n (or hardcode for local testing):
   `APP1TRANSCRIBE_URL`, `APP1TRANSCRIBE_API_KEY`, `GROQ_API_KEY`,
   `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WEBHOOK_API_KEY`
   — the last one must match your `.env` exactly.
6. Add a Set or Code node before the Groq call to assemble the final prompt
   string (system prompt + business rules + last 5-10 messages + current
   message) — this mirrors `prompts/prompt_builder.py`.
7. Verify the "Wait for human approval" resume URL matches what `/approve`
   calls in `backend/routes/approve.py`.

## Known gaps to verify before Day 2

- App1Transcribe's actual request/response contract — the code assumes
  `POST audio file -> {"text": "..."}` per the client's spec doc, untested
  against the real API.
- The exact WhatsApp webhook payload shape and Groq's response JSON path —
  both are written from documentation, not a live test call yet. Send one
  real test message through before trusting the field paths as-is.
- WhatsApp text messages have no `voice` flag the way Telegram does — the
  IF node currently branches on `message.type === "audio"`, which covers
  both voice notes and shared audio files; that's an acceptable MVP
  simplification but worth knowing.
