#!/bin/bash

# Default configuration
DEFAULT_CONTEXT_LENGTH=4096
DEFAULT_PARALLEL_INSTANCES=3

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--context)
            CONTEXT_LENGTH="$2"
            shift 2
            ;;
        -p|--parallel)
            PARALLEL_INSTANCES="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS] [MODEL_PATH]"
            echo "Options:"
            echo "  -c, --context CONTEXT_LENGTH    Set max context length (default: $DEFAULT_CONTEXT_LENGTH)"
            echo "  -p, --parallel INSTANCES        Set parallel instances (default: $DEFAULT_PARALLEL_INSTANCES)"
            echo "  -h, --help                      Show this help message"
            exit 0
            ;;
        *)
            MODEL_PATH="$1"
            shift
            ;;
    esac
done

# Use defaults if not specified
CONTEXT_LENGTH="${CONTEXT_LENGTH:-$DEFAULT_CONTEXT_LENGTH}"
PARALLEL_INSTANCES="${PARALLEL_INSTANCES:-$DEFAULT_PARALLEL_INSTANCES}"

# Binary path
LLAMA_SERVER="/build/bin/llama-server"

# Default model path
DEFAULT_MODEL="./models/default-model.gguf"

# Use provided model path or default
MODEL_PATH="${1:-$DEFAULT_MODEL}"

# Check if model file exists
if [ ! -f "$MODEL_PATH" ]; then
    echo "Error: Model file '$MODEL_PATH' not found"
    exit 1
fi

echo "Starting llama-server with model: $MODEL_PATH"

# Start llama-server with the specified model
tmux kill-session -t llama-server 2>/dev/null

tmux new -s llama-server -d "$LLAMA_SERVER" \
    --model "$MODEL_PATH" \
    --threads 4 \
    --port 8080 \
    --ctx-size "$CONTEXT_LENGTH" \
    --parallel "$PARALLEL_INSTANCES" \
    --no-webui