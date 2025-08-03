# Use Alpine Linux as base image
FROM alpine:latest

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    firefox \
    xvfb \
    dbus \
    ttf-freefont \
    && rm -rf /var/cache/apk/*

# Install geckodriver
RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz \
    && tar -xzf geckodriver-v0.33.0-linux64.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/geckodriver \
    && rm geckodriver-v0.33.0-linux64.tar.gz

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY src/requirements.txt ./

# Create virtual environment and install dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the debbit source code
COPY src/ ./

# Create necessary directories
RUN mkdir -p program_files/cookies \
    && mkdir -p program_files/state \
    && mkdir -p data/state

# Copy geckodriver to the expected location
RUN cp /usr/local/bin/geckodriver program_files/geckodriver

# Create a default config file if it doesn't exist
RUN if [ ! -f config.txt ]; then cp sample_config.txt config.txt; fi

# Create a non-root user for security
RUN addgroup -g 1000 debbit \
    && adduser -D -s /bin/sh -u 1000 -G debbit debbit \
    && chown -R debbit:debbit /app

# Switch to non-root user
USER debbit

# Expose port for Xvfb (if needed for debugging)
EXPOSE 99

# Set the default command
CMD ["python3", "debbit.py"] 