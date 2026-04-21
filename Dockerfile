FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    git \
    openssh-client \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml for dependency installation
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Source code will be mounted as volume, not copied

# Expose port
EXPOSE 8000

# Entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
