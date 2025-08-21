from pydantic import BaseModel, field_validator
from typing import Literal, Dict, Any

# TODO: Extract the valid agent names as a Literal
ValidAgent = Literal["Pricing Agent", "Payment Agent", "Scheduling Agent"]

# Define the Pydantic model
class RouterAgentOutput(BaseModel):
    next_agent: ValidAgent
    task: str
    context: Dict[str, Any]
    speak: str

    # Optional: custom validator to enforce any extra rules
    @field_validator("task")
    def task_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("task cannot be empty")
        return v

    @field_validator("speak")
    def speak_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("speak cannot be empty")
        return v
