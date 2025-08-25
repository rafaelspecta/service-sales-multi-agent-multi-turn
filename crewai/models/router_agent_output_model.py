from pydantic import BaseModel, field_validator
from typing import Literal, Dict, Any, Optional

# TODO: Extract the valid agent names as a Literal
ValidAgent = Literal["Pricing Agent", "Payment Agent", "Scheduling Agent", "None"]

# Define the Pydantic model
class RouterAgentOutput(BaseModel):
    next_agent: Optional[ValidAgent] = None
    task: Optional[str] = None
    context: Dict[str, Any] = {}  # default empty dict
    speak: Optional[str] = None

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
