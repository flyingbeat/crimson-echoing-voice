# Docker Setup Instructions

## Overview

This Docker setup provides a complete environment with:

- Python 3 runtime
- Java 11 (OpenJDK) for Apache Jena Fuseki
- tmux for session management
- Hot reload capability for development

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start the services
docker-compose up --build

# To run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Using Docker directly

```bash
# Build the image
docker build -t crimson-echoing-voice .

# Run with volume mounting for hot reload
docker run -it \
  -p 8080:8080 \
  -p 3030:3030 \
  -p 8000:8000 \
  -v $(pwd):/app \
  crimson-echoing-voice
```

## Services and Ports

- **Port 8080**: llama-server (AI model server)
- **Port 3030**: Apache Jena Fuseki (SPARQL endpoint)
- **Port 8000**: Python application (if it exposes a web interface)

## Development with Hot Reload

The Docker setup mounts your source code as a volume, enabling hot reload:

1. Make changes to your Python files
2. The application will automatically restart and pick up changes
3. No need to rebuild the Docker image for code changes

## Accessing Services

- **Fuseki Web Interface**: http://localhost:3030
- **llama-server**: http://localhost:8080
- **Python Application**: Depends on your application's web interface

## Troubleshooting

### Check if services are running

```bash
# Attach to the running container
docker-compose exec crimson-echoing-voice /bin/bash

# List tmux sessions
tmux list-sessions

# Attach to a specific session
tmux attach-session -t llama-server
tmux attach-session -t fuseki-server
```

### Check logs

```bash
# View all logs
docker-compose logs

# View logs for specific service
docker-compose logs crimson-echoing-voice

# Follow logs in real-time
docker-compose logs -f
```

### Restart services

```bash
# Restart everything
docker-compose restart

# Rebuild and restart
docker-compose up --build
```

## File Structure in Container

```
/app/
├── src/
│   ├── agent_v2.py          # Main Python application
│   └── handlers/            # Handler modules
├── scripts/
│   └── start_services.sh    # Service startup script
├── services/                # Java services (Fuseki, llama-cpp)
├── models/                  # AI models
└── requirements.txt         # Python dependencies
```

## Environment Variables

You can customize the behavior by setting environment variables in docker-compose.yml:

```yaml
environment:
  - CONTEXT_LENGTH=4096
  - PARALLEL_INSTANCES=3
  - SPARQL_SERVICE_NAME=atai
```
