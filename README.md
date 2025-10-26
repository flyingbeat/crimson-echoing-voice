# SPARQL Query Chatbot - 2nd Intermediate Evaluation

## Overview

A conversational agent that interprets natural language questions, transforms them into SPARQL queries, and executes them against a knowledge graph to return formatted answers. Supports both factual queries and embedding-based answers and a combination of both leveraging a local llm to provide the best answer.

## Objective

Demonstrate the chatbot can:

- Interface with Speakeasy infrastructure
- Interpret natural language questions
- Transform questions into SPARQL queries
- Execute queries and return properly formatted results
- Handle both factual and embedding-based questions

## Project Structure

```
.
├── .venv/                 # Virtual environment
├── services/             # services like sparql endpoint server
├── src/                  # source code for the agent
    ├── agent_v2.py       # Main agent implementation
├── .env                  # Environment variables
├── .gitignore            # Git ignore file
├── README.md             # This file
└── requirements.txt      # Python dependencies
```

## Setup

### .env file template

```
SPEAKEASY_USERNAME=
SPEAKEASY_PASSWORD=
```

### Starting the Agent

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install external dependencies
./scripts/download_dependencies.sh

# Create TDB2 database (only done once)
export JENA_HOME="<absolute_path_to_services/apache-jena>"
./services/apache-jena-5.6.0/bin/tdb2.tdbloader --loc ./services/Database <path_to_graph>

# start fuseki-server and llama-server
./scripts/start_services.sh

# in a different terminal start the agent
python src/agent_v2.py
```

This will start a local sparql endpoint available at [http://localhost:3030/atai/sparql](http://localhost:3030/atai/sparql) which is used by the agent to retrieve data from the knowledge graph. Additionally a local openai compatible llm server will be accessible at [http://localhost:8080]

## Query Types

### 1. Factual Answers

Questions answered directly from the knowledge graph using SPARQL queries.

**Example:** "Who is the director of Star Wars: Episode VI - Return of the Jedi?"

**Response:** "Factual response: Richard Marquand."

### 2. Embedding Answers

Questions answered using embedding-based similarity computation.

**Example:** "Who is the screenwriter of The Masked Gang: Cyprus?"

**Response:** "The answer suggested by embeddings: Cengiz Küçükayvaz."

### 3. Final Answer

Some questions may be answered using both methods.

**Question:** "When was 'The Godfather' released?"

**Response:** "It was released in 1972."
