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

# Create a startup script that runs both services and the Python app
RUN echo '#!/bin/bash\n\
echo "Starting services..."\n\
# Start the services in the background\n\
./scripts/start_services.sh &\n\
\n\
echo "Waiting for services to start..."\n\
sleep 10\n\
\n\
echo "Starting Python application..."\n\
# Start the Python application\n\
exec python src/agent_v2.py' > /app/startup.sh

RUN chmod +x /app/startup.sh

# Expose ports (adjust as needed)
EXPOSE 8080 3030 8000

# Set the default command
CMD ["/app/startup.sh"]
