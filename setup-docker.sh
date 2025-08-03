#!/bin/bash

# Setup script for debbit Docker container

echo "Setting up debbit Docker container..."

# Create necessary directories
mkdir -p cookies
mkdir -p state
mkdir -p logs

# Copy sample config if config.txt doesn't exist
if [ ! -f config.txt ]; then
    echo "Creating config.txt from sample_config.txt..."
    cp src/sample_config.txt config.txt
    echo "Please edit config.txt with your credentials and settings before running the container."
else
    echo "config.txt already exists."
fi

# Set proper permissions
chmod 755 cookies state logs
chmod 644 config.txt

echo ""
echo "Setup complete! To run debbit:"
echo "1. Edit config.txt with your credentials"
echo "2. Run: docker-compose up -d"
echo "3. View logs: docker-compose logs -f"
echo "4. Stop: docker-compose down"
echo ""
echo "Or build and run manually:"
echo "  docker build -t debbit ."
echo "  docker run -v \$(pwd)/config.txt:/app/config.txt:ro -v \$(pwd)/cookies:/app/program_files/cookies -v \$(pwd)/state:/app/program_files/state debbit" 