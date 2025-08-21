import os
from crewai import Agent, LLM

VERBOSE = bool(os.getenv("VERBOSE", "True"))

# llm = LLM(model="openai/gpt-4o-mini")

scheduling_agent = Agent(
    role="Scheduling Agent",
    goal="Book the service date and time with the client after payment is confirmed.",
    backstory="Coordinates technician schedules and books the cleaning appointment. Propose 2-3 slots if needed.",
    verbose=VERBOSE,
    # llm=llm
)