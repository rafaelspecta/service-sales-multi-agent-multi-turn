import json

from crewai import Task, Crew
from langfuse import observe

from agents.registry import AGENTS
from config.settings import VERBOSE
from crew.base_crew import crew
from models.router_agent_output_model import RouterAgentOutput

@observe()
def run_router_decision(history, user_msg) -> RouterAgentOutput:
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
        expected_output="Strict JSON with keys: next_agent, task, context, speak.",
        output_pydantic=RouterAgentOutput, # for validation
        agent=AGENTS["Router Agent"]
    )

    result = Crew(
        agents=[AGENTS["Router Agent"]],
        tasks=[decision_task],
        memory=crew.memory,
        process="sequential",
        verbose=VERBOSE
    ).kickoff()

    return result.pydantic