"""
Main API server module with UI integration.

This module provides the main entry point for the API server with UI integration.
"""

import os
import logging
import uvicorn
from src.api.env_config import EnvConfig
from src.api.endpoints import app
from src.ui.ui_server import ui_root  # Import UI to ensure it's registered

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def main():
    """Run the API server with UI integration."""
    # Load environment configuration
    env_config = EnvConfig()
    api_config = env_config.get_api_config()
    
    # Log configuration
    logger.info(f"Starting API server with UI on {api_config['host']}:{api_config['port']}")
    logger.info(f"UI available at http://{api_config['host']}:{api_config['port']}/ui")
    
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
