# Use Ubuntu as base image to get both Python and Java
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    openjdk-17-jdk \
    tmux \
    git \
    wget \
    curl \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the entire project (this will be overridden by volume mount for hot reload)
COPY . .

# Make scripts executable
RUN chmod +x scripts/start_services.sh

# Expose ports (adjust as needed)
EXPOSE 8080 3030 8000
