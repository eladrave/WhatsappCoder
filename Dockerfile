# Multi-stage build for WhatsApp-AutoCoder service
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 whatsapp-coder && \
    mkdir -p /app && \
    chown -R whatsapp-coder:whatsapp-coder /app

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/whatsapp-coder/.local

# Copy application code
COPY --chown=whatsapp-coder:whatsapp-coder . .

# Switch to non-root user
USER whatsapp-coder

# Update PATH
ENV PATH=/home/whatsapp-coder/.local/bin:$PATH

# Health check (using dynamic port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, requests; port=os.environ.get('PORT', '8080'); requests.get(f'http://localhost:{port}/health')" || exit 1

# Expose port (Cloud Run will use PORT env var)
EXPOSE 8080

# Run the application with dynamic port
CMD ["python", "start_server.py"]
