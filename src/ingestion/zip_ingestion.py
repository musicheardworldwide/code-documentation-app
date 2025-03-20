"""
Zip file ingestion module.

This module provides functionality for extracting zip files containing codebases.
"""

import os
import logging
import tempfile
import uuid
import zipfile
from typing import Optional

logger = logging.getLogger(__name__)

class ZipIngestion:
    """Handles zip file extraction and processing."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize zip ingestion.
        
        Args:
            output_dir (str, optional): Directory to store extracted files
        """
        self.output_dir = output_dir or tempfile.gettempdir()
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extract_zip(self, zip_path: str) -> str:
        """
        Extract zip file.
        
        Args:
            zip_path (str): Path to zip file
            
        Returns:
            str: Path to extracted directory
        """
        try:
            # Generate unique directory name
            unique_id = str(uuid.uuid4())[:8]
            extract_dir = os.path.join(self.output_dir, f"zip_{unique_id}")
            os.makedirs(extract_dir, exist_ok=True)
            
            # Extract zip file
            logger.info(f"Extracting zip file {zip_path} to {extract_dir}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            return extract_dir
        except Exception as e:
            logger.error(f"Error extracting zip file: {e}")
            raise Exception(f"Failed to extract zip file: {e}")
