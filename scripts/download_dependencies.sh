#!/bin/bash

LOCAL_MODEL_URL="https://huggingface.co/LiquidAI/LFM2-1.2B-RAG-GGUF/resolve/main/LFM2-1.2B-RAG-Q8_0.gguf"
LLAMA_CPP_URL="https://github.com/ggml-org/llama.cpp/releases/download/b6840/llama-b6840-bin-ubuntu-x64.zip"

# Colors for better output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to ask for user confirmation
ask_user() {
    local prompt="$1"
    local response
    
    while true; do
        echo -e "${BLUE}$prompt${NC} [y/n]: "
        read -r response
        case $response in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo -e "${RED}Please answer yes (y) or no (n).${NC}";;
        esac
    done
}

echo -e "${GREEN}=== Loading Dependencies ===${NC}"
echo "This script will download the following files:"
echo "1. LFM2-1.2B-RAG model (~1.3GB)"
echo "2. llama.cpp binary (~50MB)"
echo ""

# Create directories if they don't exist
mkdir -p ./models
mkdir -p ./tmp
mkdir -p ./services/llama-cpp

# Download local model
if ask_user "Do you want to download the LFM2-1.2B-RAG model?"; then
    echo -e "${YELLOW}Downloading LFM2-1.2B-RAG model...${NC}"
    if [ -f "./models/LFM2-1.2B-RAG-Q8_0.gguf" ]; then
        echo -e "${YELLOW}Model file already exists. Skipping download.${NC}"
    else
        wget $LOCAL_MODEL_URL -O ./models/LFM2-1.2B-RAG-Q8_0.gguf
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Model downloaded successfully!${NC}"
        else
            echo -e "${RED}Failed to download model.${NC}"
        fi
    fi
else
    echo -e "${YELLOW}Skipping model download.${NC}"
fi

echo ""

# Download llama.cpp binary
if ask_user "Do you want to download the llama.cpp binary?"; then
    echo -e "${YELLOW}Downloading llama.cpp binary...${NC}"
    if [ -f "./services/llama-cpp/bin/llama-server" ]; then
        echo -e "${YELLOW}llama.cpp binary already exists. Skipping download.${NC}"
    else
        wget $LLAMA_CPP_URL -O ./tmp/llama-cpp.zip
        if [ $? -eq 0 ]; then
            echo -e "${YELLOW}Extracting llama.cpp binary...${NC}"
            unzip ./tmp/llama-cpp.zip -d ./services/llama-cpp/
            chmod +x ./services/llama-cpp/bin/llama-server
            echo -e "${GREEN}llama.cpp binary downloaded and extracted successfully!${NC}"
            # Clean up zip file
            rm ./tmp/llama-cpp.zip
        else
            echo -e "${RED}Failed to download llama.cpp binary.${NC}"
        fi
    fi
else
    echo -e "${YELLOW}Skipping llama.cpp binary download.${NC}"
fi

echo ""
echo -e "${GREEN}=== Dependency loading complete ===${NC}"
