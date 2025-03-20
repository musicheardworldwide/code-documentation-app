#!/bin/bash

# Script to run the API server
echo "Starting Code Documentation API server..."

# Create data directories if they don't exist
mkdir -p data/output data/temp data/vector_db

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Using default configuration."
    echo "Consider creating a .env file based on .env.example for custom configuration."
fi

# Run the API server
python -m src.api.server
