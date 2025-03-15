# Docker Guide

## What is Docker?

Docker is a platform that uses containerization technology to package applications and their dependencies together in isolated containers. These containers are lightweight, portable units that can run consistently across different environments.

### Key Docker Concepts

- **Container**: A lightweight, standalone executable package that includes everything needed to run an application
- **Image**: A read-only template used to create containers
- **Dockerfile**: A script with instructions for building a Docker image
- **Docker Compose**: A tool for defining and running multi-container applications
- **Volume**: Persistent data storage that exists outside the container lifecycle

### Benefits of Using Docker with Acestream Scraper

1. **Simplified Installation**: No need to worry about dependencies or system compatibility
2. **Consistent Environment**: Works the same way on any system that supports Docker
3. **Built-in Services**: Easily includes Acestream Engine, ZeroNet, and Acexy proxy
4. **Isolation**: Keeps the application and its dependencies contained
5. **Easy Updates**: Simple command to update to the latest version
6. **Resource Management**: Controls how much system resources the application can use

## Docker vs. Docker Compose

### Docker
- Manages individual containers
- Best for simple deployments
- Uses CLI commands to configure containers
- Example: `docker run -p 8000:8000 pipepito/acestream-scraper:latest`

### Docker Compose
- Manages multi-container applications
- Configuration in a YAML file
- Easier to maintain complex setups
- Example: `docker-compose up -d`

For Acestream Scraper, Docker Compose is recommended as it makes managing all configuration parameters easier.

## Basic Docker Commands

### Pull the Image
```bash
docker pull pipepito/acestream-scraper:latest
```

### Run the Container
```bash
docker run -d -p 8000:8000 --name acestream-scraper pipepito/acestream-scraper:latest
```

### View Running Containers
```bash
docker ps
```

### View Container Logs
```bash
docker logs acestream-scraper
```

### Stop the Container
```bash
docker stop acestream-scraper
```

### Remove the Container
```bash
docker rm acestream-scraper
```

### Update to Latest Version
```bash
docker pull pipepito/acestream-scraper:latest
docker stop acestream-scraper
docker rm acestream-scraper
# Run the container again with your preferred configuration
```

## Docker Compose Commands

### Start Services
```bash
docker-compose up -d
```

### View Logs
```bash
docker-compose logs
```

### Stop Services
```bash
docker-compose down
```

### Update to Latest Version
```bash
docker-compose pull
docker-compose up -d
```

## Docker Data Persistence

Acestream Scraper uses Docker volumes to persist data:

- `/app/config`: Configuration files including database
- `/app/ZeroNet/data`: ZeroNet data directory (if using ZeroNet)

These volumes should be mounted to local directories to ensure your data persists when containers are updated or replaced.

Example:
```bash
docker run -d -p 8000:8000 -v "${PWD}/config:/app/config" pipepito/acestream-scraper:latest
```

This mounts your local `./config` directory to the container's `/app/config` directory.
