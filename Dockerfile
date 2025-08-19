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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Create startup script for dynamic port binding
RUN cat > /app/start_server.py << 'EOF'
import os
import sys
import uvicorn

# Get port from Cloud Run
port = int(os.environ.get("PORT", 8080))
print(f"Starting server on port {port}", flush=True)

# Import the app
from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
EOF

# Run the application with dynamic port
CMD ["python", "/app/start_server.py"]
