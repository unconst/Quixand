FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install minimal system dependencies
# gcc is needed for compiling some Python packages
# git is needed for pip to install from git repositories
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY uv.lock* ./
COPY README.md ./
COPY quixand/ ./quixand/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv && \
    uv pip install --system -e .

# Install Python SDK for Docker and Podman (no CLI needed)
RUN pip install --no-cache-dir \
    docker \
    podman

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV QS_RUNTIME=docker
ENV DOCKER_HOST=unix:///var/run/docker.sock

# Create mount point for Docker socket
VOLUME ["/var/run/docker.sock"]

# Default command - run Python with Quixand available
CMD ["python"]