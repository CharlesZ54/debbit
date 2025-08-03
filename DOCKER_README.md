# Debbit Docker Container

This Docker setup allows you to run debbit in a containerized environment using Alpine Linux as the base image.

## Quick Start

1. **Create the data directory:**
   ```bash
   mkdir -p data/state
   ```

2. **Create configuration file:**
   ```bash
   cp src/sample_config.txt data/config.txt
   nano data/config.txt  # or use your preferred editor
   ```

3. **Build the image:**
   ```bash
   docker build -t debbit .
   ```

4. **Run the container:**
   ```bash
   docker run -d --name debbit -v $(pwd)/data:/app/data debbit
   ```

5. **View logs:**
   ```bash
   docker logs -f debbit
   ```

6. **Stop the container:**
   ```bash
   docker stop debbit && docker rm debbit
   ```

## GitHub Actions & Docker Hub

This repository includes GitHub Actions that automatically build and push Docker images to Docker Hub when you commit to the master branch.

### Setup Docker Hub Integration

1. **Create a Docker Hub account** (if you don't have one)
2. **Create a Docker Hub repository** named `charlesz54/debbit`
3. **Generate a Docker Hub access token:**
   - Go to Docker Hub → Account Settings → Security
   - Click "New Access Token"
   - Give it a name like "GitHub Actions"
   - Copy the token

4. **Add GitHub Secrets:**
   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Add these secrets:
     - `DOCKERHUB_USERNAME`: Your Docker Hub username (`charlesz54`)
     - `DOCKERHUB_TOKEN`: Your Docker Hub access token

### Automatic Builds

Once set up, every push to the master branch will:
- Build the Docker image
- Push it to `charlesz54/debbit` on Docker Hub
- Tag it with `latest` and semantic versions

### Using the Published Image

After the GitHub Action runs, you can pull and run the image directly:

```bash
# Pull the latest image
docker pull charlesz54/debbit:latest

# Run without building locally
docker run -d --name debbit -v $(pwd)/data:/app/data charlesz54/debbit:latest
```

## One-Time Run

For testing or one-time execution:

```bash
# Build and run once
docker build -t debbit .
docker run --rm -v $(pwd)/data:/app/data debbit
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
docker logs debbit
```

### Firefox issues
The container uses Xvfb for headless Firefox. If you encounter display issues, try:
```bash
docker stop debbit && docker rm debbit
docker run -d --name debbit -v $(pwd)/data:/app/data debbit
```

### OTP (One-Time Password) Handling

When the container encounters an OTP prompt, it will pause and provide instructions for providing the OTP:

1. **Using the helper script (recommended):**
   ```bash
   ./provide_otp.sh debbit merchant_id 123456
   ```

2. **Using docker exec directly:**
   ```bash
   docker exec -it debbit python3 -c "import debbit; debbit.provide_otp('merchant_id', '123456')"
   ```

3. **Using interactive docker exec:**
   ```bash
   docker exec -it debbit bash -c 'echo "Enter OTP: " && read otp && python3 -c "import debbit; debbit.provide_otp(\"merchant_id\", \"$otp\")"'
   ```

**Note:** Replace `merchant_id` with the actual merchant identifier (e.g., `amazon_gift_card_reload`) and `123456` with the actual OTP code.

### Permission issues
Make sure the mounted directories have proper permissions:
```bash
chmod 755 data data/state
chmod 644 data/config.txt
```

**Note:** These permissions are automatically set when you create the directories and files.

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