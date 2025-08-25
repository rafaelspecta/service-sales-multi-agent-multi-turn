from typing import Dict, Any
from datetime import date
from langfuse import observe

SESSIONS: Dict[str, Dict[str, Any]] = {}

@observe()
def get_session(chat_id: str) -> Dict[str, Any]:
    if chat_id not in SESSIONS:
        today=date.today().strftime("%Y%m%d")
        SESSIONS[chat_id] = {"history": "", "trace_id": f"{chat_id}-{today}"}
    return SESSIONS[chat_id]