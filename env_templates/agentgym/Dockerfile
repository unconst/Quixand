FROM python:3.11-slim

# Install system dependencies including additional build tools
RUN apt-get update && apt-get install -y \
    gcc cmake build-essential \
    g++ libffi-dev \
    git \
    curl \
    wget \
    patch \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone AgentGym repository
RUN git clone https://github.com/WooooDyy/AgentGym.git

# Set build argument for environment name
ARG PREINSTALL_ENV=""
ENV ENV_NAME=${PREINSTALL_ENV}

COPY install_env.py /app/
COPY env.py /app/

# Install base dependencies
RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic

# Upgrade pip and setuptools to handle newer packages
RUN pip install --upgrade pip setuptools wheel

# Run installation script if environment is specified
RUN if [ -n "$PREINSTALL_ENV" ]; then \
        ENV_NAME=$PREINSTALL_ENV python /app/install_env.py || \
        echo "Warning: Some dependencies failed to install, continuing..."; \
    fi

# Set environment variable for alfworld data
ENV ALFWORLD_DATA=/root/.cache/alfworld

WORKDIR /sandbox

# Start the FastAPI server
CMD ["uvicorn", "env:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "/app"]