"""
Main module for loading environment variables.

This module provides the main entry point for loading environment variables.
"""

import os
import sys
import logging
from src.api.env_config import EnvConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def load_environment(env_file=None):
    """
    Load environment variables.
    
    Args:
        env_file (str, optional): Path to .env file
        
    Returns:
        EnvConfig: Environment configuration
    """
    # If env_file is not provided, try to find .env file
    if not env_file:
        # Check for .env file in current directory
        if os.path.exists(".env"):
            env_file = ".env"
        # Check for .env file in parent directory
        elif os.path.exists(os.path.join("..", ".env")):
            env_file = os.path.join("..", ".env")
        # Check for .env file in application directory
        elif os.path.exists(os.path.join(os.path.dirname(__file__), "..", "..", ".env")):
            env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    
    # Load environment variables
    env_config = EnvConfig(env_file)
    
    # Set log level from environment
    log_level = env_config.log_level
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    # Log configuration
    logger.info(f"Environment loaded from {env_file if env_file else 'default locations'}")
    
    return env_config
