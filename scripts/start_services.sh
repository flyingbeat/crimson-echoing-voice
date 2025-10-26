#!/bin/bash

# Default configuration
CONTEXT_LENGTH=4096
PARALLEL_INSTANCES=3

# Use defaults if not specified
CONTEXT_LENGTH="${CONTEXT_LENGTH:-$CONTEXT_LENGTH}"
PARALLEL_INSTANCES="${PARALLEL_INSTANCES:-$PARALLEL_INSTANCES}"

# Binary path
LLAMA_SERVER="./services/llama-cpp/build/bin/llama-server"
FUSEKI_SERVER="./services/apache-jena-fuseki-5.6.0/fuseki-server"

# Default model path
MODEL="./models/LFM2-1.2B-RAG-Q8_0.gguf"

# SPARQL service name
SPARQL_SERVICE_NAME="atai"

echo "Starting llama-server with model: $MODEL, context length: $CONTEXT_LENGTH, parallel instances: $PARALLEL_INSTANCES on port 8080"

# Start llama-server with the specified model
tmux kill-session -t llama-server 2>/dev/null

tmux new -s llama-server -d "$LLAMA_SERVER" \
    --model "$MODEL" \
    --threads 4 \
    --port 8080 \
    --ctx-size "$CONTEXT_LENGTH" \
    --parallel "$PARALLEL_INSTANCES" \
    --no-webui

# start fuseki-server
echo "Starting fuseki-server with service name: $SPARQL_SERVICE_NAME"
tmux kill-session -t fuseki-server 2>/dev/null

tmux new -s fuseki-server -d "$FUSEKI_SERVER --loc=./services/Database/ $SPARQL_SERVICE_NAME"