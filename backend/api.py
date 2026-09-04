from fastapi import FastAPI

from backend.routes import approve, health, webhook
from database.database import init_db

app = FastAPI(title="WhatsApp AI Assistant Backend")


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(approve.router)
