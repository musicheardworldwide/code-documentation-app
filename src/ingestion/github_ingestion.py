"""
GitHub repository ingestion module.

This module provides functionality for cloning GitHub repositories.
"""

import os
import logging
import tempfile
import uuid
from typing import Optional
import git

logger = logging.getLogger(__name__)

class GitHubIngestion:
    """Handles GitHub repository cloning and processing."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize GitHub ingestion.
        
        Args:
            output_dir (str, optional): Directory to store cloned repositories
        """
        self.output_dir = output_dir or tempfile.gettempdir()
        os.makedirs(self.output_dir, exist_ok=True)
    
    def clone_repository(self, repo_url: str) -> str:
        """
        Clone GitHub repository.
        
        Args:
            repo_url (str): GitHub repository URL
            
        Returns:
            str: Path to cloned repository
        """
        try:
            # Generate unique directory name
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            unique_id = str(uuid.uuid4())[:8]
            repo_dir = os.path.join(self.output_dir, f"{repo_name}_{unique_id}")
            
            # Clone repository
            logger.info(f"Cloning repository {repo_url} to {repo_dir}")
            git.Repo.clone_from(repo_url, repo_dir)
            
            return repo_dir
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            raise Exception(f"Failed to clone repository: {e}")
