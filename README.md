# SPARQL Query Chatbot - 3nd Intermediate Evaluation

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
├── .venv/                # Virtual environment
├── services/             # services like sparql endpoint server
├── src/                  # source code for the agent
    ├── main.py           # entry point
    ├── /**               # python modules
├── docker-compose.yml    # docker service definitions
├── .env                  # Environment variables
├── .gitignore            # Git ignore file
├── README.md             # This file
└── requirements.txt      # Python dependencies
```

## Setup

### Prerequisites

To run fuseki server you need

- python3
- java (for nuvolos: `conda install -c conda-forge openjdk=21`)

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

# create graph data for multimedia queries
python ./scripts/create_image_graph.py /space_mounts/atai-hs25/dataset/additional/images.json -o ./services/images.nt

# Create TDB2 database (only done once or when graph changes)
export JENA_HOME="./services/apache-jena-5.6.0" # path to apache jena
./services/apache-jena-5.6.0/bin/tdb2.tdbloader --loc ./services/Database /space_mounts/atai-hs25/dataset/graph.nt ./services/images.nt # local path to two graphs

# start fuseki-server and llama-server
./scripts/start_services.sh

# in a different terminal start the agent
python src/agent.py
```

or with docker

```bash
docker compose up --build -d
```

This will start a local sparql endpoint available at [http://localhost:3030/atai/sparql](http://localhost:3030/atai/sparql) which is used by the agent to retrieve data from the knowledge graph. Additionally a local openai compatible llm server will be accessible at [http://localhost:8080]

## Recommendation Questions

### 1. Factual Answers

Questions answered directly from the knowledge graph using SPARQL queries.

**Example:** "Given that I like The Lion King, Pocahontas, and The Beauty and the Beast, can you recommend some movies?"

**Response:** "<Adequate recommendations will be (2-D) animated movies or real-life remakes of Disney movies.>"
