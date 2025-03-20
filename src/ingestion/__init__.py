"""
Module initialization file.

This file initializes the ingestion module.
"""

# Import submodules
from src.ingestion.github_ingestion import GitHubIngestion
from src.ingestion.zip_ingestion import ZipIngestion
from src.ingestion.file_detection import FileDetector

__all__ = ['GitHubIngestion', 'ZipIngestion', 'FileDetector']
