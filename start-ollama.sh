#!/bin/bash

# Set environment variables
export OLLAMA_HOST=0.0.0.0
export OLLAMA_ORIGINS=*

# Start Ollama in the background
ollama serve &

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
until curl -s http://localhost:11434/api/version > /dev/null; do
    sleep 1
done
echo "Ollama is ready!"

# Function to pull model with retries
pull_model() {
    local model=$1
    local max_retries=3
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        echo "Pulling $model model (attempt $((retry + 1))/$max_retries)..."
        if ollama pull $model; then
            echo "$model pulled successfully!"
            return 0
        fi
        retry=$((retry + 1))
        if [ $retry -lt $max_retries ]; then
            echo "Failed to pull $model, retrying in 10 seconds..."
            sleep 10
        fi
    done
    
    echo "Failed to pull $model after $max_retries attempts"
    return 1
}

# Pull required models
pull_model "llama3.2" || exit 1
pull_model "nomic-embed-text" || exit 1

echo "All models pulled successfully!"

# Keep the container running
tail -f /dev/null 