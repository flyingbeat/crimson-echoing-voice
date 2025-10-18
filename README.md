# SPARQL Query Chatbot - 1st Intermediate Evaluation

## Overview

A conversational agent that executes SPARQL queries against a knowledge graph and returns formatted answers.

## Objective

Demonstrate the chatbot can:

- Interface with Speakeasy infrastructure
- Parse and execute SPARQL queries
- Return properly formatted results

## Project Structure

```
.
├── venv/                  # Virtual environment
├── .env                   # Environment variables
├── .gitignore            # Git ignore file
├── agent_v1.py           # Main agent implementation
├── README.md             # This file
└── requirements.txt      # Python dependencies
```

### .env file template

```
SPEAKEASY_USERNAME=
SPEAKEASY_PASSWORD=
```

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# start agent
python agent_v1.py
```

## Example Queries

**Highest rated movie:**

```sparql
SELECT ?movieLabel ?movieItem WHERE {
    ?movieItem wdt:P31 wd:Q11424 .
    ?movieItem ddis:rating ?rating .
    ?movieItem rdfs:label ?movieLabel .
}
ORDER BY DESC(?rating) LIMIT 1
```

Response: `Acidulous Midtime Shed (Q10850238456619979)`

**Movie director:**

```sparql
SELECT ?directorLabel ?directorItem WHERE {
    ?movieItem rdfs:label "The Bridge on the River Kwai" .
    ?movieItem wdt:P57 ?directorItem .
    ?directorItem rdfs:label ?directorLabel .
}
```

Response: `David Lean (Q55260)`

**Multiple results (producers):**

```sparql
SELECT ?producerLabel ?producerItem WHERE {
    ?movieItem rdfs:label "French Kiss" .
    ?movieItem wdt:P162 ?producerItem .
    ?producerItem rdfs:label ?producerLabel .
}
```

Response:

```
Tim Bevan (Q1473065)
Meg Ryan (Q167498)
Eric Fellner (Q1351291)
```

## Evaluation Criteria

- ✓ Correct query execution
- ✓ Speakeasy integration
- ✓ Proper result formatting
- ✓ Handle various query types

## Dependencies

See `requirements.txt`:

- `rdflib` - RDF/SPARQL processing
- Additional packages for Speakeasy integration
