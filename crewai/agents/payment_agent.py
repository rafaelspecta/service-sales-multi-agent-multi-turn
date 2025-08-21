import os
from crewai import Agent, LLM

VERBOSE = bool(os.getenv("VERBOSE", "True"))

# llm = LLM(model="openai/gpt-4o-mini")

payment_agent = Agent(
    role="Payment Agent",
    goal="Charge the customer for the service and confirm the transaction.",
    backstory=(
        "Handles payments securely and confirms to the Router when payment is done.\n"
        "You must:\n"
        "* Generate a payment link for the agreed service.\n"
        "* Track payment confirmation.\n"
        "* Provide the payment status to the customer.\n"
        "If payment systems are not integrated yet, simulate a link and status."
    ),
    allow_delegation=True,
    verbose=VERBOSE,
    # llm=llm
)