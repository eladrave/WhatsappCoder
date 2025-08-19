#!/usr/bin/env python3
"""
Startup script for dynamic port binding in Google Cloud Run
"""

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
