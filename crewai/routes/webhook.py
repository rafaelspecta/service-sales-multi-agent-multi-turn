from fastapi import APIRouter, Request, HTTPException
from langfuse import observe

from config.settings import ALLOW_LIST
from config.observability import langfuse
from crew.multi_turn_runner import run_multi_turn
from services.evolution import parse_evolution_event, send_evolution_text

router = APIRouter()

@router.post("/webhook/evolution")
@observe(name="New chat message")
async def evolution_webhook(req: Request):
    try:
        body = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    parsed = parse_evolution_event(body)
    if not parsed:
        # Not a user message; ack silently
        return {"ok": True}

    chat_id = parsed["chat_id"]
    number = parsed["number"]
    user_msg = parsed["message"]

    print("----------------------------------")
    print(f"Chat ID: {chat_id}")
    print(f"Number: {number}")
    print(f"Message: {user_msg}")

    # if number in allow_list and not user_msg.startswith("Sales Agent:"):
    if number in ALLOW_LIST and not user_msg.startswith("Sales Agent:"):
        # Run one hierarchical turn
        reply_text = run_multi_turn(chat_id, user_msg)

        # Send back via Evolution
        send_evolution_text(number, f"Sales Agent: {reply_text}") # Temporary solution to avoid processing Sales Agent message since it is the same number
        # send_evolution_text(number, reply_text)

        # TODO: Humanize: Show "Writing" - NOTE: Not working when sending from the same phone number
        # send_evolution_presence(number, "composing", 2000)

        # try:
        #     # TODO: Humanize: Hold message for a few seconds
        #     time.sleep(max(3000, 0) / 1000.0)
        # finally:
        #     send_evolution_text(
        #         number,
        #         text = (
        #             "Sales Agent: NEED HELP\n"
        #             f"Number: {number}\n"
        #             f"Last Message: {user_msg}\n"
        #             f"Summary/Situation:\n sample summary"
        #         )
        #     )

        langfuse.update_current_trace(
            input=user_msg,
            output=reply_text
        )
    elif user_msg.startswith("Sales Agent:"):
        print("Ignoring Supervisor message")
    else:
        print("Ignoring all other numbers")

    return {"ok": True}