# Frameworks

* ADK (Google Agent Development Framework)
* AG2 (fork from Microsoft's AutoGen)
* Agent Squad (AWS)
* AutoGen (Microsoft)
* CrewAI
* LangChain
* LangGraph (LangChain)
* LlamaIndex
* smolAgents (Hugging Face)
* Swarm (OpenAI)

# Run minimal requirements

## Langfuse

Suggetion: Do this outside of this root folder

```
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up
```

Access: http://localhost:3000

## Evolution API

Starting from the root folder

1) Create .env file based on the sample version. There is no need to change any env var on this file.
```
cp env-sample .env
```

2) Start the containers
```
docker compose up -d
```

Access: http://localhost:8080/manager

# CrewAI

Starting from the root folder

```
cd crewai
```

1) Create .env file based on the sample version and fill the variables
```
cp env-sample .env
```

2) Create the environment
```
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

3) Install the requirements
```
uv pip install -r requirements.txt
```

4) Run the application
```
fastapi dev main.py
```