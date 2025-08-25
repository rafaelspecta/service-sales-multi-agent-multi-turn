from crewai import Crew
from agents.registry import AGENTS

crew = Crew(
    agents=list(AGENTS.values()),
    tasks=[],
    memory=True,
    cache=False,
    process="sequential",
)