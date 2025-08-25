import os
from dotenv import load_dotenv

load_dotenv()

VERBOSE = bool(os.getenv("VERBOSE", "True"))

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_INSTANCE_ID = os.getenv("EVOLUTION_INSTANCE_ID")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")

ALLOW_LIST = os.getenv("ALLOW_LIST", "").split(",") if os.getenv("ALLOW_LIST") else []

SALES_AGENT_PHONE_NUMBER = os.getenv("SALES_AGENT_PHONE_NUMBER")

