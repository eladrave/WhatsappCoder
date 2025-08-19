#!/usr/bin/env python3
"""
Startup script for dynamic port binding in Google Cloud Run
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

try:
    import uvicorn
    logger.info("uvicorn imported successfully")
except ImportError as e:
    logger.error(f"Failed to import uvicorn: {e}")
    sys.exit(1)

# Get port from Cloud Run
port = int(os.environ.get("PORT", 8080))
logger.info(f"Starting server on port {port}")

try:
    # Import the app
    from app.main import app
    logger.info("App imported successfully")
except ImportError as e:
    logger.error(f"Failed to import app: {e}")
    logger.error("Make sure all dependencies are installed")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error importing app: {e}")
    sys.exit(1)

if __name__ == "__main__":
    try:
        logger.info(f"Starting uvicorn on 0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
