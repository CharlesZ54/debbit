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
echo "2. Run: docker-compose up -d"
echo "3. View logs: docker-compose logs -f"
echo "4. Stop: docker-compose down"
echo ""
echo "Or build and run manually:"
echo "  docker build -t debbit ."
echo "  docker run -v \$(pwd)/data:/app/data debbit" 