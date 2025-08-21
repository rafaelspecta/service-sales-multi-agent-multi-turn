import json
import os
from crewai.tools import tool
from whatsapp.whatsapp import send_evolution_text

SALES_AGENT_PHONE_NUMBER = os.getenv("SALES_AGENT_PHONE_NUMBER")

@tool("escalate_to_human")
def escalate_to_human(payload: str) -> str:
    """
    Use when the crew is not confident, out-of-scope, or user explicitly asks for a human.
    Payload should be a short JSON string with:
      { "reason": "...", "last_user_message": "...", "context": "..." }
    """

    try:
        data = json.loads(payload)
    except Exception:
        data = {"payload": payload}

    send_evolution_text(
        SALES_AGENT_PHONE_NUMBER,
        text = (
            "Sales Agent: NEED HELP\n"
            # f"Number: {number}\n"
            f"Reason: {data['reason']}\n"
            f"Last Message: {data['last_user_message']}\n"
            f"Context:\n {data['context']}"
        )
    )