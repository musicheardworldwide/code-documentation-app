"""
Environment variable handling module.

This module provides functionality for loading and accessing environment variables.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class EnvConfig:
    """Environment configuration handler."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize environment configuration.
        
        Args:
            env_file (str, optional): Path to .env file
        """
        # Load environment variables from .env file if provided
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"Loaded environment variables from {env_file}")
        else:
            # Try to load from default locations
            load_dotenv()
            logger.info("Loaded environment variables from default locations")
        
        # LLM API Configuration
        self.llm_base_url = os.getenv("LLM_BASE_URL", "https://api.example.com")
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_instruct_model = os.getenv("LLM_INSTRUCT_MODEL", "instruct_model")
        self.llm_reasoning_model = os.getenv("LLM_REASONING_MODEL", "reasoning_model")
        self.llm_embeddings_model = os.getenv("LLM_EMBEDDINGS_MODEL", "embeddings_model")
        
        # Application Configuration
        self.output_dir = os.getenv("OUTPUT_DIR", "documentation_output")
        self.temp_dir = os.getenv("TEMP_DIR", "/tmp/code_documentation")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # API Configuration
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.api_workers = int(os.getenv("API_WORKERS", "4"))
        self.api_debug = os.getenv("API_DEBUG", "false").lower() == "true"
        self.api_cors_origins = os.getenv("API_CORS_ORIGINS", "*").split(",")
        self.api_rate_limit = int(os.getenv("API_RATE_LIMIT", "100"))
        
        # Database Configuration
        self.vector_db_path = os.getenv("VECTOR_DB_PATH", "vector_db")
    
    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get LLM configuration.
        
        Returns:
            Dict[str, Any]: LLM configuration
        """
        return {
            "base_url": self.llm_base_url,
            "api_key": self.llm_api_key,
            "instruct_model": self.llm_instruct_model,
            "reasoning_model": self.llm_reasoning_model,
            "embeddings_model": self.llm_embeddings_model
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """
        Get API configuration.
        
        Returns:
            Dict[str, Any]: API configuration
        """
        return {
            "host": self.api_host,
            "port": self.api_port,
            "workers": self.api_workers,
            "debug": self.api_debug,
            "cors_origins": self.api_cors_origins,
            "rate_limit": self.api_rate_limit
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        Get all configuration.
        
        Returns:
            Dict[str, Any]: All configuration
        """
        return {
            "llm": self.get_llm_config(),
            "app": {
                "output_dir": self.output_dir,
                "temp_dir": self.temp_dir,
                "log_level": self.log_level
            },
            "api": self.get_api_config(),
            "db": {
                "vector_db_path": self.vector_db_path
            }
        }
