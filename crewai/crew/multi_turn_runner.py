from langfuse import observe
import traceback

from agents.registry import AGENTS
from config.observability import langfuse
from config.settings import VERBOSE
from crew.router_runner import run_router_decision
from crew.session import get_session
from crew.specialist_runner import run_specialist
from models.router_agent_output_model import RouterAgentOutput

@observe()
def run_multi_turn(chat_id: str, user_input: str) -> str:
    session = get_session(chat_id)
    history_note = session["history"]

    agent_name = None

    # Wire Langfuse session
    try:
        langfuse.update_current_trace(session_id=session["trace_id"],user_id=chat_id)
    except Exception as e:
        print(f"Langfuse update_current_trace failed: {e}")

    try:
        decision: RouterAgentOutput = run_router_decision(history_note, user_input)

        agent_name = decision.next_agent

        # if agent_name in agents:
        if agent_name in AGENTS:
            try:
                result = run_specialist(agent_name, decision.task, decision.context)
            except Exception as e:
                print(f"Specialist ({agent_name}) ERROR: {e}")
                print(e)
                agent_name = "Manager Router Agent"
                result = "Sorry, I had trouble deciding next step. Could you rephrase?"
        else:
            agent_name = "Manager Router Agent"
            result = decision.speak or "I didn't understand your request."

    except Exception as e:
        error_details = traceback.format_exc()
        print("Error details:\n", error_details)

        agent_name = "Manager Router Agent"
        result = "Sorry, I had trouble deciding next step. Could you rephrase?"

    if type(result) is str:
        final_text = result
    else:
        # CrewAI return from run_specialist is a CrewOutput; extract best-effort final text
        final_text = getattr(result, "final_output", None) or str(getattr(result, "raw", ""))    

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