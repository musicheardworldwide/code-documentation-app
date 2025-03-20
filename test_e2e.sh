#!/bin/bash

# End-to-end test script for code documentation app
# This script tests the application with a sample GitHub repository

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting end-to-end test for code documentation app${NC}"

# Check if .env file exists, create it if not
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file with default values${NC}"
    cat > .env << EOF
OLLAMA_BASE_URL=http://localhost:11434
INSTRUCT_MODEL=llama2
REASONING_MODEL=llama2
EMBEDDINGS_MODEL=llama2
GITHUB_TOKEN=
LOG_LEVEL=INFO
MAX_TOKENS=2048
TEMPERATURE=0.7
TOP_P=0.9
EOF
    echo -e "${GREEN}.env file created${NC}"
else
    echo -e "${GREEN}.env file already exists${NC}"
fi

# Check if Ollama is installed and running
echo -e "${YELLOW}Checking Ollama installation${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}Ollama is not installed. Please install Ollama first:${NC}"
    echo -e "${YELLOW}curl -fsSL https://ollama.com/install.sh | sh${NC}"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/version &> /dev/null; then
    echo -e "${RED}Ollama is not running. Please start Ollama:${NC}"
    echo -e "${YELLOW}ollama serve${NC}"
    exit 1
fi

echo -e "${GREEN}Ollama is installed and running${NC}"

# Check if required models are available
echo -e "${YELLOW}Checking if required models are available${NC}"
source .env
if ! curl -s "http://localhost:11434/api/tags" | grep -q "$INSTRUCT_MODEL"; then
    echo -e "${YELLOW}Pulling $INSTRUCT_MODEL model...${NC}"
    ollama pull $INSTRUCT_MODEL
fi

if [ "$REASONING_MODEL" != "$INSTRUCT_MODEL" ] && ! curl -s "http://localhost:11434/api/tags" | grep -q "$REASONING_MODEL"; then
    echo -e "${YELLOW}Pulling $REASONING_MODEL model...${NC}"
    ollama pull $REASONING_MODEL
fi

if [ "$EMBEDDINGS_MODEL" != "$INSTRUCT_MODEL" ] && [ "$EMBEDDINGS_MODEL" != "$REASONING_MODEL" ] && ! curl -s "http://localhost:11434/api/tags" | grep -q "$EMBEDDINGS_MODEL"; then
    echo -e "${YELLOW}Pulling $EMBEDDINGS_MODEL model...${NC}"
    ollama pull $EMBEDDINGS_MODEL
fi

echo -e "${GREEN}All required models are available${NC}"

# Create test output directory
TEST_OUTPUT_DIR="./test_output"
rm -rf $TEST_OUTPUT_DIR
mkdir -p $TEST_OUTPUT_DIR

# Test with a small GitHub repository
echo -e "${YELLOW}Testing with a small GitHub repository${NC}"
TEST_REPO="https://github.com/microsoft/vscode-extension-samples"

echo -e "${YELLOW}Running code documentation app...${NC}"
python main.py --github $TEST_REPO --output-dir $TEST_OUTPUT_DIR

# Verify output
echo -e "${YELLOW}Verifying documentation output${NC}"
if [ ! -f "$TEST_OUTPUT_DIR/index.html" ]; then
    echo -e "${RED}Documentation index.html not found!${NC}"
    exit 1
fi

if [ ! -f "$TEST_OUTPUT_DIR/summary.md" ]; then
    echo -e "${RED}Documentation summary.md not found!${NC}"
    exit 1
fi

if [ ! -f "$TEST_OUTPUT_DIR/development_qa.md" ]; then
    echo -e "${RED}Development Q&A not found!${NC}"
    exit 1
fi

echo -e "${GREEN}Documentation verification successful!${NC}"

# Test API server
echo -e "${YELLOW}Testing API server${NC}"
# Start API server in background
./run_api.sh &
API_PID=$!

# Wait for API server to start
echo -e "${YELLOW}Waiting for API server to start...${NC}"
sleep 5

# Test API endpoints
echo -e "${YELLOW}Testing API endpoints${NC}"
if ! curl -s http://localhost:8000/api/v1/health | grep -q "status"; then
    echo -e "${RED}API health endpoint failed!${NC}"
    kill $API_PID
    exit 1
fi

echo -e "${GREEN}API health endpoint successful!${NC}"

# Stop API server
echo -e "${YELLOW}Stopping API server${NC}"
kill $API_PID

# Test Docker build
echo -e "${YELLOW}Testing Docker build${NC}"
if ! docker build -t code-documentation-app:test .; then
    echo -e "${RED}Docker build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Docker build successful!${NC}"

echo -e "${GREEN}All tests passed successfully!${NC}"
echo -e "${GREEN}End-to-end test completed${NC}"
