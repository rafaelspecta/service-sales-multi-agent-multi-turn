import os
from crewai import Agent, LLM

from tools.escalate_to_human import escalate_to_human

VERBOSE = bool(os.getenv("VERBOSE", "True"))

# llm = LLM(model="openai/gpt-4o-mini")

# note: Eslacation Agent could have been a tool linked to Manager Agent
escalation_agent = Agent(
    role="Escalation Agent",
    # goal="When requested by the manager, notify a human sales agent and acknowledge the customer with a ticket id.",
    goal="When requested by the manager, notify a human sales agent.",
    backstory=(
        "Use the 'escalate_to_human' tool with a compact JSON payload containing: "
        "reason, last_user_message, and context (brief summary). "
    ),
    tools=[escalate_to_human],
    verbose=VERBOSE,
    # llm=llm
)
