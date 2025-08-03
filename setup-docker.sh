#!/bin/bash

# Setup script for debbit Docker container

echo "Setting up debbit Docker container..."

# Create data directory structure
mkdir -p data/state

# Copy sample config if data/config.txt doesn't exist
if [ ! -f data/config.txt ]; then
    echo "Creating data/config.txt from sample_config.txt..."
    cp src/sample_config.txt data/config.txt
    echo "Please edit data/config.txt with your credentials and settings before running the container."
else
    echo "data/config.txt already exists."
fi

# Set proper permissions
chmod 755 data data/state
chmod 644 data/config.txt

echo ""
echo "Setup complete! To run debbit:"
echo "1. Edit data/config.txt with your credentials"
echo "2. Build: docker build -t debbit ."
echo "3. Run: docker run -d --name debbit -v \$(pwd)/data:/app/data debbit"
echo "4. View logs: docker logs -f debbit"
echo "5. Stop: docker stop debbit && docker rm debbit"
echo ""
echo ""
echo "For one-time run (not daemon):"
echo "  docker run --rm -v \$(pwd)/data:/app/data debbit" 