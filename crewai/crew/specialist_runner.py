from crewai import Task, Crew
from langfuse import observe

from agents.registry import AGENTS
from config.settings import VERBOSE
from models.router_agent_output_model import RouterAgentOutput

from .base_crew import crew

@observe()
def run_specialist(agent_name, task_text, context_text):

    coworker_task = Task(
        description=f"{task_text}\n\nContext:\n{context_text}\n",
        expected_output="One final message to the user.",
        agent=AGENTS[agent_name]
    )

    specialist_crew = Crew(
        agents=[AGENTS[agent_name]],
        tasks=[coworker_task],
        # memory=crew.memory,
        process="sequential",
        verbose=VERBOSE
    )

    return specialist_crew.kickoff()