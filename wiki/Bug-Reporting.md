# Bug Reporting Guide

Encountering bugs is an inevitable part of software development. This guide will help you report bugs effectively so they can be resolved quickly.

## Before Reporting a Bug

Before submitting a new bug report, please:

1. **Update to the latest version** - Many bugs are fixed in newer releases:
   ```bash
   # If using Docker Compose
   docker-compose pull
   docker-compose up -d
   
   # If using Docker directly
   docker pull pipepito/acestream-scraper:latest
   docker stop acestream-scraper
   docker rm acestream-scraper
   # Then run your container again with the same configuration
   ```

2. Check the [FAQ](FAQ.md) to see if your issue is already addressed
3. Search existing [GitHub Issues](https://github.com/Pipepito/acestream-scraper/issues) to avoid duplicates
4. Try basic troubleshooting steps mentioned in the FAQ

## Required Information

### Version Details

Always include the exact version you're using:

- **Docker image tag**: (e.g., `pipepito/acestream-scraper:latest`, `pipepito/acestream-scraper:1.2.3`)
  ```bash
  docker inspect pipepito/acestream-scraper:latest | grep "Image ID"
  ```
  
- **Version in web interface**: Check the footer of the web interface which should display the current version

### Environment Information

- **Operating System**: (e.g., Ubuntu 22.04, Windows 11, macOS 13)
- **Docker version**:
  ```bash
  docker --version
  ```
- **Docker Compose version** (if applicable):
  ```bash
  docker-compose --version
  ```
- **Browser and version** (if UI-related): (e.g., Chrome 114, Firefox 115)

### Deployment Method

Describe how you deployed the application:

- Docker Compose
- Direct Docker run command
- Manual installation
- Include your `docker-compose.yml` file or Docker run command with sensitive information removed

### Problem Description

1. **Clear summary**: A concise description of the issue
2. **Steps to reproduce**: Numbered, specific steps that lead to the bug
   ```
   1. Navigate to http://localhost:8000
   2. Click on "Add URL"
   3. Enter URL: example.com
   4. Click submit
   ```
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Frequency**: Does it happen every time or intermittently?
6. **Screenshots**: If applicable, especially for UI issues

## How to Collect Logs

Logs are crucial for diagnosing issues. Here's how to collect them:

### Docker Container Logs

```bash
# Last 100 lines
docker logs --tail 100 acestream-scraper

# All logs since container start
docker logs acestream-scraper > acestream-scraper-logs.txt

# Logs with timestamps
docker logs --timestamps acestream-scraper
```

### Application-Specific Logs

The application logs are stored inside the container at `/app/logs`:

```bash
# Copy logs from container to host
docker cp acestream-scraper:/app/logs ./acestream-scraper-logs

# View specific log file
docker exec acestream-scraper cat /app/logs/app.log
```

### Health Check Information

```bash
curl http://localhost:8000/health
```

## Common Debugging Steps

Try these steps to gather more information about your issue:

1. **Check Acestream Engine status**:
   ```bash
   curl http://localhost:6878/server/version
   ```

2. **Check Acexy status** (if enabled):
   ```bash
   curl http://localhost:8080/ace/status
   ```

3. **Check database integrity**:
   ```bash
   docker exec acestream-scraper python -c "from app.extensions import db; print('Database connection:', db.engine.connect())"
   ```

4. **Verify network connectivity** (if channels are offline):
   ```bash
   docker exec acestream-scraper ping -c 3 google.com
   ```

## Submitting Your Bug Report

1. Go to [GitHub Issues](https://github.com/Pipepito/acestream-scraper/issues)
2. Click "New Issue"
3. Choose "Bug Report" template if available
4. Fill in the details using the information you've gathered
5. Use a descriptive title that summarizes the issue
6. Submit the issue

## Bug Report Template

Use this template to structure your bug report:
