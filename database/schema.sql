CREATE TABLE IF NOT EXISTS conversations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id     TEXT NOT NULL,
    sender_name   TEXT,
    channel       TEXT NOT NULL DEFAULT 'whatsapp',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id       INTEGER NOT NULL REFERENCES conversations(id),
    direction             TEXT NOT NULL CHECK (direction IN ('incoming', 'outgoing')),
    message_type          TEXT NOT NULL CHECK (message_type IN ('text', 'voice')),
    original_text         TEXT,
    transcript            TEXT,
    platform_message_id   TEXT UNIQUE,   -- WhatsApp message id; enforces idempotency against duplicate webhook deliveries
    timestamp             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_replies (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id         INTEGER NOT NULL REFERENCES messages(id),
    generated_reply    TEXT NOT NULL,
    edited_reply       TEXT,
    status             TEXT NOT NULL DEFAULT 'pending_review'
                        CHECK (status IN (
                            'received','transcribing','transcribed','generating_ai',
                            'pending_review','approved','sending','sent','failed','rejected'
                        )),
    confidence_score   REAL,
    n8n_resume_url     TEXT,
    n8n_execution_id   TEXT,
    n8n_workflow_id    TEXT,
    retry_count        INTEGER NOT NULL DEFAULT 0,
    edited_by          TEXT,
    edited_at          DATETIME,
    input_tokens       INTEGER,
    output_tokens      INTEGER,
    api_cost           REAL,
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at            DATETIME
);

CREATE TABLE IF NOT EXISTS prompt_versions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    version_label  TEXT NOT NULL,
    file_reference TEXT NOT NULL,
    created_by     TEXT,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active      BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    level      TEXT NOT NULL,
    source     TEXT NOT NULL,
    message    TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
