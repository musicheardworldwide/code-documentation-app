"""
Zip ingestion module with complete implementation.

This module provides functionality for extracting and analyzing zip files containing code.
"""

import os
import logging
import tempfile
import shutil
import zipfile
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ZipIngestion:
    """Handles ingestion of zip files containing code."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize zip ingestion.
        
        Args:
            temp_dir (str, optional): Temporary directory for extracting zip files
        """
        self.temp_dir = temp_dir or os.path.join(tempfile.gettempdir(), "code_documentation", "zip")
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def extract_zip(self, zip_path: str) -> Dict[str, Any]:
        """
        Extract zip file.
        
        Args:
            zip_path (str): Path to zip file
            
        Returns:
            Dict[str, Any]: Extraction information
        """
        try:
            logger.info(f"Extracting zip file: {zip_path}")
            
            # Validate zip file
            if not os.path.exists(zip_path):
                raise FileNotFoundError(f"Zip file not found: {zip_path}")
            
            if not zipfile.is_zipfile(zip_path):
                raise ValueError(f"Not a valid zip file: {zip_path}")
            
            # Extract zip file name
            zip_name = os.path.basename(zip_path)
            if zip_name.endswith(".zip"):
                zip_name = zip_name[:-4]
            
            # Create unique directory for this zip file
            extract_dir = os.path.join(self.temp_dir, zip_name)
            
            # Remove directory if it already exists
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            
            os.makedirs(extract_dir, exist_ok=True)
            
            # Extract zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Check for malicious paths (path traversal)
                for file_info in zip_ref.infolist():
                    file_path = file_info.filename
                    if file_path.startswith('/') or '..' in file_path:
                        raise ValueError(f"Potentially malicious path in zip file: {file_path}")
                
                # Extract all files
                zip_ref.extractall(extract_dir)
            
            # Get extraction information
            extraction_info = {
                "name": zip_name,
                "path": extract_dir,
                "original_zip": zip_path,
                "size": self._get_directory_size(extract_dir),
                "file_count": self._count_files(extract_dir)
            }
            
            logger.info(f"Zip file extracted successfully: {extract_dir}")
            return extraction_info
        except Exception as e:
            logger.error(f"Error extracting zip file: {e}")
            raise Exception(f"Failed to extract zip file: {e}")
    
    def analyze_extraction(self, extraction_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze extracted code structure.
        
        Args:
            extraction_info (Dict[str, Any]): Extraction information
            
        Returns:
            Dict[str, Any]: Extraction analysis
        """
        try:
            logger.info(f"Analyzing extracted code structure: {extraction_info['path']}")
            
            extract_path = extraction_info["path"]
            
            # Get file count
            file_count = extraction_info.get("file_count", 0)
            if file_count == 0:
                file_count = self._count_files(extract_path)
            
            # Get directory count
            dir_count = 0
            for root, dirs, _ in os.walk(extract_path):
                dir_count += len(dirs)
            
            # Detect common project files
            has_readme = self._find_file(extract_path, ["README.md", "README"])
            has_license = self._find_file(extract_path, ["LICENSE", "LICENSE.md"])
            has_gitignore = self._find_file(extract_path, [".gitignore"])
            has_package_json = self._find_file(extract_path, ["package.json"])
            has_requirements_txt = self._find_file(extract_path, ["requirements.txt"])
            has_setup_py = self._find_file(extract_path, ["setup.py"])
            has_dockerfile = self._find_file(extract_path, ["Dockerfile"])
            has_docker_compose = self._find_file(extract_path, ["docker-compose.yml", "docker-compose.yaml"])
            
            # Detect programming languages
            languages = self._detect_languages(extract_path)
            
            # Create extraction analysis
            extraction_analysis = {
                "file_count": file_count,
                "directory_count": dir_count,
                "has_readme": has_readme,
                "has_license": has_license,
                "has_gitignore": has_gitignore,
                "has_package_json": has_package_json,
                "has_requirements_txt": has_requirements_txt,
                "has_setup_py": has_setup_py,
                "has_dockerfile": has_dockerfile,
                "has_docker_compose": has_docker_compose,
                "languages": languages
            }
            
            logger.info(f"Extraction analysis completed: {extract_path}")
            return extraction_analysis
        except Exception as e:
            logger.error(f"Error analyzing extraction: {e}")
            raise Exception(f"Failed to analyze extraction: {e}")
    
    def cleanup(self, extraction_info: Optional[Dict[str, Any]] = None):
        """
        Clean up temporary files.
        
        Args:
            extraction_info (Dict[str, Any], optional): Extraction information
        """
        try:
            if extraction_info and "path" in extraction_info:
                # Remove specific extraction
                extract_path = extraction_info["path"]
                if os.path.exists(extract_path):
                    logger.info(f"Removing extraction: {extract_path}")
                    shutil.rmtree(extract_path)
            else:
                # Remove all extractions
                logger.info(f"Removing all extractions in: {self.temp_dir}")
                if os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir)
                    os.makedirs(self.temp_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Error cleaning up: {e}")
    
    def _get_directory_size(self, path: str) -> int:
        """
        Get directory size in bytes.
        
        Args:
            path (str): Directory path
            
        Returns:
            int: Directory size in bytes
        """
        total_size = 0
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        return total_size
    
    def _count_files(self, path: str) -> int:
        """
        Count files in directory.
        
        Args:
            path (str): Directory path
            
        Returns:
            int: File count
        """
        file_count = 0
        for root, _, files in os.walk(path):
            file_count += len(files)
        return file_count
    
    def _find_file(self, path: str, filenames: List[str]) -> bool:
        """
        Find file in directory.
        
        Args:
            path (str): Directory path
            filenames (List[str]): List of filenames to find
            
        Returns:
            bool: True if any file is found, False otherwise
        """
        for root, _, files in os.walk(path):
            for filename in filenames:
                if filename in files:
                    return True
        return False
    
    def _detect_languages(self, path: str) -> Dict[str, int]:
        """
        Detect programming languages in directory.
        
        Args:
            path (str): Directory path
            
        Returns:
            Dict[str, int]: Language counts
        """
        language_extensions = {
            "python": [".py", ".pyx", ".pyi"],
            "javascript": [".js", ".jsx", ".mjs"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hxx"],
            "csharp": [".cs"],
            "go": [".go"],
            "ruby": [".rb"],
            "php": [".php"],
            "swift": [".swift"],
            "rust": [".rs"],
            "kotlin": [".kt", ".kts"],
            "scala": [".scala"],
            "html": [".html", ".htm"],
            "css": [".css"],
            "shell": [".sh", ".bash"],
            "sql": [".sql"],
            "markdown": [".md", ".markdown"],
            "json": [".json"],
            "yaml": [".yml", ".yaml"],
            "xml": [".xml"],
            "dockerfile": ["Dockerfile"],
            "other": []
        }
        
        language_counts = {lang: 0 for lang in language_extensions}
        
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    # Check if file matches any language
                    matched = False
                    for lang, extensions in language_extensions.items():
                        if file in extensions or any(file.endswith(ext) for ext in extensions):
                            language_counts[lang] += 1
                            matched = True
                            break
                    
                    # Count as other if no match
                    if not matched:
                        language_counts["other"] += 1
        
        # Remove languages with zero count
        return {lang: count for lang, count in language_counts.items() if count > 0}
