from langfuse import get_client
from openinference.instrumentation.crewai import CrewAIInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor

CrewAIInstrumentor().instrument(skip_dep_check=True)
LiteLLMInstrumentor().instrument()

langfuse = get_client()
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Langfuse auth failed. Check credentials and host.")