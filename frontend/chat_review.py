"""
Run with: streamlit run frontend/chat_review.py
Requires the FastAPI backend to already be running (backend/api.py) since this
page talks to it over HTTP, exactly like n8n does.
"""
import sys
from pathlib import Path

# Streamlit runs this script from frontend/'s own folder, not the project root,
# so config.py and database/ (both at the root) can't be found without this.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
import streamlit as st

from config import settings
from database import database as db

st.set_page_config(page_title="WhatsApp AI Assistant — Review", layout="centered")
st.title("Pending replies")

API_BASE = f"http://localhost:{settings.backend_port}"
HEADERS = {"X-API-Key": settings.webhook_api_key}

if st.button("Refresh"):
    st.rerun()

pending = db.get_pending_replies()

if not pending:
    st.info("No replies waiting for review.")

for reply in pending:
    with st.container(border=True):
        st.caption(f"From {reply['sender_name'] or reply['sender_id']} · {reply['message_type']}")

        if reply["message_type"] == "voice":
            st.write("**Transcript:**", reply["transcript"])
        else:
            st.write("**Message:**", reply["original_text"])

        edited = st.text_area(
            "AI-suggested reply (edit if needed)",
            value=reply["generated_reply"],
            key=f"reply_{reply['id']}",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Approve & send", key=f"approve_{reply['id']}"):
                resp = requests.post(
                    f"{API_BASE}/approve/{reply['id']}",
                    json={"edited_reply": edited, "edited_by": "operator"},
                    headers=HEADERS,
                    timeout=20,
                )
                if resp.ok:
                    st.success("Approved — n8n is sending the reply.")
                    st.rerun()
                else:
                    st.error(f"Failed to approve: {resp.text}")
        with col2:
            if st.button("Reject", key=f"reject_{reply['id']}"):
                resp = requests.post(f"{API_BASE}/reject/{reply['id']}", headers=HEADERS, timeout=10)
                if resp.ok:
                    st.warning("Rejected.")
                    st.rerun()
                else:
                    st.error(f"Failed to reject: {resp.text}")