FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Allows to set the node environment
ARG ENVIRONMENT
ENV ENVIRONMENT=${ENVIRONMENT:-production}

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Install index-now command to PATH
RUN chmod +x /app/index-now && \
    cp /app/index-now /usr/local/bin/index-now

# Create non-root user and change ownership
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

# Use entrypoint script to support different run modes
ENTRYPOINT ["/app/entrypoint.sh"]
CMD []
