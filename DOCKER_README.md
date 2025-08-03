# Debbit Docker Container

This Docker setup allows you to run debbit in a containerized environment using Alpine Linux as the base image.

## Quick Start

1. **Setup the environment:**
   ```bash
   ./setup-docker.sh
   ```

2. **Edit the configuration:**
   ```bash
   nano data/config.txt  # or use your preferred editor
   ```

3. **Run with docker-compose:**
   ```bash
   docker-compose up -d
   ```

4. **View logs:**
   ```bash
   docker-compose logs -f
   ```

5. **Stop the container:**
   ```bash
   docker-compose down
   ```

## Manual Docker Commands

If you prefer to use Docker directly:

```bash
# Build the image
docker build -t debbit .

# Run the container
docker run -d \
  --name debbit \
  -v $(pwd)/data:/app/data \
  debbit

# View logs
docker logs -f debbit

# Stop the container
docker stop debbit
docker rm debbit
```

## Configuration

The container expects a `data/config.txt` file in the current directory. The setup script will create this from the sample configuration if it doesn't exist.

### Volume Mounts

- `data/`: Single directory containing:
  - `config.txt`: Your debbit configuration file
  - `state/`: Directory for debbit state files

## Features

- **Alpine Linux base**: Lightweight and secure
- **Firefox + Geckodriver**: Full browser automation support
- **Xvfb**: Headless display for Firefox
- **Non-root user**: Security best practices
- **Health checks**: Container monitoring
- **Data persistence**: Cookies and state preserved across restarts

## Troubleshooting

### Container won't start
Check the logs:
```bash
docker-compose logs
```

### Firefox issues
The container uses Xvfb for headless Firefox. If you encounter display issues, try:
```bash
docker-compose down
docker-compose up --force-recreate
```

### Permission issues
Make sure the mounted directories have proper permissions:
```bash
chmod 755 data data/state
chmod 644 data/config.txt
```

### Configuration issues
Verify your `data/config.txt` file is properly formatted and contains valid credentials.

## Building from Source

To build the image from the current source:

```bash
docker build -t debbit:latest .
```

## Security Notes

- The container runs as a non-root user (`debbit`)
- Configuration files are mounted as read-only
- No unnecessary packages are installed
- Alpine Linux provides a minimal attack surface

## Performance

The Alpine-based image is lightweight (~200MB) and starts quickly. The container includes all necessary dependencies for running debbit in a headless environment. 