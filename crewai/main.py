import os
from dotenv import load_dotenv

import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException

from crewai import Crew, Task, Agent, LLM, Process
from crewai.tools import tool
from langfuse import get_client
from langfuse import observe

from pydantic import RootModel

from models.router_agent_output_model import RouterAgentOutput

from agents.router_agent import router_agent
from agents.pricing_agent import pricing_agent
from agents.service_info_agent import service_info_agent
from agents.payment_agent import payment_agent
from agents.scheduling_agent import scheduling_agent
from agents.escalation_agent import escalation_agent

from whatsapp.whatsapp import parse_evolution_event, send_evolution_text

# Optional OpenInference instrumentation for CrewAI/LiteLLM
from openinference.instrumentation.crewai import CrewAIInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor
CrewAIInstrumentor().instrument(skip_dep_check=True)
LiteLLMInstrumentor().instrument()

# ------------------------------------------------------------------------------
# Env & Config
# ------------------------------------------------------------------------------

# Load the .env file
load_dotenv()

VERBOSE = bool(os.getenv("VERBOSE", "True"))

# SALES_AGENT_PHONE_NUMBER = os.getenv("SALES_AGENT_PHONE_NUMBER")

# Evolution API config
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_INSTANCE_ID = os.getenv("EVOLUTION_INSTANCE_ID")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")  # header 'apikey'

ALLOW_LIST = os.getenv("ALLOW_LIST", "")
allow_list = ALLOW_LIST.split(",") if ALLOW_LIST else []

# ------------------------------------------------------------------------------
# Observability init
# ------------------------------------------------------------------------------

langfuse = get_client()
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Langfuse auth failed. Check credentials and host.")

# ------------------------------------------------------------------------------
# LLM
# ------------------------------------------------------------------------------
llm = LLM(model="openai/gpt-4o-mini")


agents = {
    "Pricing Agent": pricing_agent,
    "Payment Agent": payment_agent,
    "Scheduling Agent": scheduling_agent,
    "Service Information Agent": service_info_agent,
    "Escalation Agent": escalation_agent
}

# ------------------------------------------------------------------------------
# Persistent Crew - for persistent memory
# ------------------------------------------------------------------------------
# TODO: Change to mem0 memory
crew = Crew(
    agents=[router_agent, pricing_agent, payment_agent, scheduling_agent, service_info_agent, escalation_agent],
    tasks=[],  # no preloaded tasks
    memory=True,
    cache=False,
    process="sequential" # note: Hierarchical processing does not work - it is never aware of the other agents
)

# ------------------------------------------------------------------------------
# In-memory session store for short-term history by chat id
# In production, prefer Redis/DB.
# ------------------------------------------------------------------------------
SESSIONS: Dict[str, Dict[str, Any]] = {}

def get_session(chat_id: str) -> Dict[str, Any]:
    if chat_id not in SESSIONS:
        SESSIONS[chat_id] = {
            "history": "",
            "trace_id": chat_id,
        }
    return SESSIONS[chat_id]

# ------------------------------------------------------------------------------
# Supporting runners
# ------------------------------------------------------------------------------
@observe()
def run_router_decision(history, user_msg):
    decision_task = Task(
        description=(
            "# Conversation summary so far:\n"
            f"{history}\n"
            "# New user message:\n"
            "\n"
            f"{user_msg}\n"
            "\n"
            "# Return Instructions:\n"
            "\n"
            "Return ONLY the JSON decision as specified. No extra text."
        ),
        expected_output='Strict JSON with keys: next_agent, task, context, speak.',
        output_model=RouterAgentOutput, # for validation
        agent=router_agent
    )

    result = Crew(
        agents=[router_agent],
        tasks=[decision_task],
        memory=crew.memory,
        process="sequential",
        verbose=VERBOSE
    ).kickoff()

    return json.loads(result.raw)

@observe()
def run_specialist(agent_name, task_text, context_text):

    coworker_task = Task(
        description=f"{task_text}\n\nContext:\n{context_text}\n",
        expected_output="One final message to the user.",
        agent=agents[agent_name]
    )

    specialist_crew = Crew(
        agents=[agents[agent_name]],
        tasks=[coworker_task],
        # memory=crew.memory,
        process="sequential",
        verbose=VERBOSE
    )

    return specialist_crew.kickoff()

# ------------------------------------------------------------------------------
# Core runner: one message into hierarchical crew
# ------------------------------------------------------------------------------
@observe()
def run_multi_turn(chat_id: str, user_input: str) -> str:
    session = get_session(chat_id)
    history_note = session["history"]

    agent_name = None

    # Wire Langfuse session
    try:
        langfuse.update_current_trace(session_id=session["trace_id"])
    except Exception as e:
        print(f"Langfuse update_current_trace failed: {e}")

    try:
        decision = run_router_decision(history_note, user_input)

        agent_name = decision.get("next_agent")

        if agent_name in agents:
            try:
                result = run_specialist(agent_name, decision.get("task", ""), decision.get("context", ""))
            except Exception as e:
                print(f"Specialist ({agent_name}) ERROR: {e}")
                print(e)
                agent_name = "Manager Router Agent"
                result = "Sorry, I had trouble deciding next step. Could you rephrase?"
        else:
            agent_name = "Manager Router Agent"
            result = decision.get("speak") or "I didn't understand your request."

    except Exception as e:
        print(f"Router Decision ERROR: {e}")
        agent_name = "Manager Router Agent"
        result = "Sorry, I had trouble deciding next step. Could you rephrase?"

    # CrewAI returns a ProcessResult; extract best-effort final text
    final_text = getattr(result, "final_output", None) or str(getattr(result, "raw", "")) or str(result)

    print(f"{agent_name}:\n```\n{final_text}\n```\n")

    # Persist a compact running summary (you can compress or summarize if needed)
    session["history"] += (
        "\n"
        # User Message
        "User:\n"
        "```\n"
        f"{user_input}\n"
        "```\n"
        "\n"
        # Agent Response
        f"{agent_name}:\n"
        "```\n"
        f"{final_text}\n"
        "```\n"
    )

    return final_text

# ------------------------------------------------------------------------------
# FastAPI server
# ------------------------------------------------------------------------------
app = FastAPI()

# Keep flexible for varying payloads; accept any JSON
class EvolutionWebhookRequest(RootModel[Dict[str, Any]]):
    pass

@app.post("/webhook/evolution")
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

    if number in allow_list and not user_msg.startswith("Sales Agent:"):
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
    elif user_msg.startswith("Sales Agent:"):
        print("Ignoring Supervisor message")
    else:
        print("Ignoring all other numbers")

    return {"ok": True}

# Health check
@app.get("/health")
def health():
    return {"status": "up"}
