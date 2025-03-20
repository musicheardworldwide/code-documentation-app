"""
API server module.

This module provides the main entry point for the API server.
"""

import os
import logging
import uvicorn
from src.api.env_config import EnvConfig
from src.api.endpoints import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def main():
    """Run the API server."""
    # Load environment configuration
    env_config = EnvConfig()
    api_config = env_config.get_api_config()
    
    # Log configuration
    logger.info(f"Starting API server on {api_config['host']}:{api_config['port']}")
    
    # Run server
    uvicorn.run(
        "src.api.endpoints:app",
        host=api_config["host"],
        port=api_config["port"],
        workers=api_config["workers"],
        reload=api_config["debug"]
    )

if __name__ == "__main__":
    main()
