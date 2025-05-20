FROM mcr.microsoft.com/devcontainers/python:3.12

# Install uv (Rustも必要)
RUN apt-get update && apt-get install -y curl build-essential && \
    curl -LsSf https://astral.sh/uv/install.sh | sh

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
